"""Execute byte-preserved V1 in a fresh process and disposable filesystem."""
from __future__ import annotations

import hashlib
from importlib.util import find_spec
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = ROOT / "engine" / "historical" / "v1"
CASE_ROOT = ROOT / "synthetic_cases"
RECOVERY = ROOT / "engine" / "recovery-manifest.json"
TIMEOUT_SECONDS = 45
MAX_INPUT_BYTES = 500_000
MAX_RESULT_BYTES = 3_000_000

def dependency_path() -> str:
    """Resolve installed engine dependencies, not caller-controlled PYTHONPATH."""
    roots = set()
    for name in ("pypdf", "PIL", "yaml"):
        spec = find_spec(name)
        if spec is None or not spec.origin:
            raise ExecutionFailed("Required Python dependency is unavailable.")
        roots.add(str(Path(spec.origin).resolve().parent.parent))
    return os.pathsep.join(sorted(roots))

class InputRejected(ValueError):
    """No uploaded text, paths, profiles, or arbitrary case IDs are accepted."""

class ExecutionFailed(RuntimeError):
    """Public-safe execution failure; never expose stderr or local paths."""

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify_historical() -> str:
    manifest = json.loads(RECOVERY.read_text(encoding="utf-8"))
    for entry in manifest["v1_files"]:
        path = HISTORICAL / entry["path"]
        if not path.is_file() or digest(path.read_bytes()) != entry["sha256"]:
            raise ExecutionFailed("Historical engine integrity check failed.")
    return digest(json.dumps(
        [(entry["path"], entry["sha256"]) for entry in manifest["v1_files"]],
        separators=(",", ":"),
    ).encode())

def cases() -> list[dict]:
    return json.loads((CASE_ROOT / "manifest.json").read_text(encoding="utf-8"))["cases"]

def case_detail(case_id: str) -> dict:
    for item in cases():
        if item["case_id"] == case_id:
            return item
    raise InputRejected("Choose a case from the approved synthetic manifest.")

def validate_sources(case: dict) -> list[tuple[dict, bytes]]:
    validated = []
    for document in case["documents"]:
        filename = document["filename"]
        if (document["synthetic"] is not True or Path(filename).name != filename
                or "/" in filename or "\\" in filename
                or Path(filename).suffix.lower() not in {".txt", ".md", ".pdf"}):
            raise InputRejected("Invalid approved source manifest.")
        path = CASE_ROOT / case["case_id"] / filename
        if path.is_symlink() or not path.is_file():
            raise InputRejected("Approved source is unavailable.")
        data = path.read_bytes()
        if len(data) > MAX_INPUT_BYTES or digest(data) != document["sha256"]:
            raise InputRejected("Approved source integrity check failed.")
        if filename.endswith(".pdf"):
            from io import BytesIO
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted or len(reader.pages) != document["expected_page_count"]:
                raise InputRejected("Unsupported approved PDF.")
            # Do not invoke historical Windows OCR on the web runtime.
            if any(len((page.extract_text() or "").strip()) < 25 for page in reader.pages):
                raise InputRejected("OCR-required PDFs are outside this release.")
        elif document["expected_page_count"] != 1:
            raise InputRejected("Text documents must declare one logical text record.")
        validated.append((document, data))
    return validated

def execute_v11(workspace: Path, child_env: dict, remaining: float, upstream_digest: str) -> dict:
    custody_path = ROOT / "engine" / "v11-custody.json"
    custody = json.loads(custody_path.read_text(encoding="utf-8"))
    recovered = ROOT / "engine" / "historical" / "v1_1"
    for entry in custody["files"]:
        if digest((recovered / entry["path"]).read_bytes()) != entry["adapted_sha256"]:
            raise ExecutionFailed("Recovered V1.1 integrity check failed.")
    stage = workspace / "v11"
    shutil.copytree(workspace / "src", stage / "src")
    for entry in custody["files"]:
        shutil.copyfile(recovered / entry["path"], stage / entry["path"])
    shutil.copytree(workspace / "data", stage / "data")
    shutil.copytree(workspace / "data" / "processed_json", stage / "processed_json")
    shutil.copyfile(ROOT / "engine" / "runtime" / "v11_stage.py", stage / "v11_stage.py")
    if remaining <= 0:
        raise ExecutionFailed("Analysis exceeded the bounded execution time.")
    try:
        child_start = time.monotonic()
        completed = subprocess.run([sys.executable, "-B", str(stage / "v11_stage.py")],
            cwd=stage, env=child_env, capture_output=True, timeout=remaining)
    except subprocess.TimeoutExpired:
        raise ExecutionFailed("Analysis exceeded the bounded execution time.") from None
    except OSError:
        raise ExecutionFailed("Recovered V1.1 execution could not start.") from None
    if completed.returncode:
        raise ExecutionFailed("Recovered V1.1 processing failed; no prepared result was substituted.")
    try:
        analytical = json.loads((stage / "v11-result.json").read_text(encoding="utf-8"))
        execution = json.loads((stage / "v11-execution.json").read_text(encoding="utf-8"))
        execution["subprocess_seconds"] = round(time.monotonic() - child_start, 6)
    except (OSError, ValueError):
        raise ExecutionFailed("Recovered V1.1 required output is missing.") from None
    analytical.update(engine_identity=digest(custody_path.read_bytes()),
                      adaptation_identity=custody["adaptation_id"], upstream_v1_sha256=upstream_digest)
    encoded = json.dumps(analytical, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {**analytical, "result_sha256": digest(encoded.encode()), "execution": execution}


def execute(case_id: str, *, include_v11: bool = True) -> dict:
    clock = time.monotonic()
    case = case_detail(case_id)
    source_bytes = validate_sources(case)
    engine_hash = verify_historical()
    run_id = str(uuid4())
    started = datetime.now(timezone.utc).isoformat()
    # Fresh process avoids Python's module cache and imported global path leakage.
    # Config resolves relative to its byte-identical copy inside this unique root.
    with tempfile.TemporaryDirectory(prefix="neverlost-v2-") as directory:
        workspace = Path(directory)
        shutil.copytree(HISTORICAL / "src", workspace / "src",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        raw = workspace / "data" / "raw_documents"
        raw.mkdir(parents=True)
        for document, data in source_bytes:
            (raw / document["filename"]).write_bytes(data)
        # Do not inherit API keys, Vercel credentials, or local profile configuration.
        child_env = {key: value for key, value in os.environ.items()
                     if key in {"PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL"}}
        child_env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
        # Serverless dependencies are vendored outside the interpreter's default
        # site-packages. Pass only resolved dependency roots, never the parent env.
        child_env["PYTHONPATH"] = dependency_path()
        try:
            child_start = time.monotonic()
            completed = subprocess.run(
                [sys.executable, "-B", str(workspace / "src" / "main.py")],
                cwd=workspace, env=child_env, capture_output=True, timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise ExecutionFailed("Analysis exceeded the bounded execution time.") from None
        except OSError:
            raise ExecutionFailed("Python execution could not start.") from None
        if completed.returncode:
            raise ExecutionFailed("Historical Python execution failed; no prepared result was substituted.")
        v1_seconds = time.monotonic() - child_start
        try:
            processed = workspace / "data" / "processed_json"
            names = ["events", "timeline", "evidence_matrix", "hidden_states",
                     "trust_thresholds", "bottlenecks", "capacity_windows", "chunks"]
            artifacts = {name: json.loads((processed / f"{name}.json").read_text(encoding="utf-8"))
                         for name in names}
            pages = json.loads((workspace / "data" / "extracted_text" / "extracted_pages.json")
                               .read_text(encoding="utf-8"))
            reports = {p.name: p.read_text(encoding="utf-8")
                       for p in sorted((workspace / "outputs" / "reports").glob("*.md"))}
        except (OSError, ValueError):
            raise ExecutionFailed("Historical execution did not produce the required artifacts.") from None
        if not reports:
            raise ExecutionFailed("No generated reports were produced.")
        # Approved text-bearing inputs must never enter the platform-specific OCR path.
        if any(page.get("ocr_required") for page in pages):
            raise ExecutionFailed("Unexpected OCR requirement; no analysis is presented.")
        sources = []
        for document, _ in source_bytes:
            sources.append({**document, "pages": [
                {"page": page["page"], "text": page["text"],
                 "text_extraction_method": page["text_extraction_method"]}
                for page in pages if page["document"] == document["filename"]
            ]})
        payload = {"artifacts": artifacts, "reports": reports, "sources": sources}
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode()) > MAX_RESULT_BYTES:
            raise ExecutionFailed("Generated output exceeded the bounded response size.")
        # Normal execution artifacts must not contain the transient execution root.
        if str(workspace) in encoded or str(workspace).replace("\\", "/") in encoded:
            raise ExecutionFailed("Generated output contained an internal runtime path.")
        result = {
            "run_id": run_id, "case_id": case_id, "status": "completed",
            "started": started, "completed": datetime.now(timezone.utc).isoformat(),
            "engine": {"v1": engine_hash, "v1_1": "not_integrated",
                       "runtime": "v2-isolated-subprocess-1"},
            "result_sha256": digest(encoded.encode()),
            "counts": {"documents": len(sources), "pages": len(pages),
                       **{name: len(value) for name, value in artifacts.items()}},
            "warnings": [
                "Historical heuristic outputs require human review; they are not clinical conclusions.",
                "Historical keyword rules can misread negation, including 'not approved'. No correction is silently applied.",
                "Historical reports contain template language and may overgeneralize beyond the supplied evidence.",
                "Historical references are preserved; missing relationships are not inferred.",
                "V1.1 live processing is not integrated. Final-synthesis generation remains unestablished.",
                "This response is ephemeral. Runs are not durably stored; refresh requires another execution.",
                "Historical 'AI/rule-based' report labels do not indicate LLM execution; the LLM interface is disabled.",
            ],
            **payload,
        }
        if include_v11:
            result["v1_1"] = execute_v11(workspace, child_env,
                TIMEOUT_SECONDS - (time.monotonic() - clock), result["result_sha256"])
            result["engine"]["v1_1"] = result["v1_1"]["engine_identity"]
            result["engine"]["runtime"] = "v2-isolated-subprocess-2"
            result["warnings"][4] = "Recovered V1.1 runs after V1; publication adaptations are explicit. Final synthesis remains unestablished."
        result["completed"] = datetime.now(timezone.utc).isoformat()
        result["execution_metrics"] = {"combined_seconds": round(time.monotonic() - clock, 6),
                                       "v1_subprocess_seconds": round(v1_seconds, 6),
                                       "memory": "Not measured on this platform"}
        combined = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        if len(combined.encode()) > MAX_RESULT_BYTES:
            raise ExecutionFailed("Generated output exceeded the bounded response size.")
        if str(workspace) in combined or str(workspace).replace("\\", "/") in combined:
            raise ExecutionFailed("Generated output contained an internal runtime path.")
    # TemporaryDirectory has removed source copies and all outputs before returning.
    return result
