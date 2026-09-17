"""Explicit preview-only verification; credentials remain in the Vercel CLI.

Run from the repository root with --cli pointing to the installed vercel entry.
No response, private path, or authentication cookie is written to disk.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.runtime.adapter import execute


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--cli", required=True)
    args = parser.parse_args()
    host = urlparse(args.url).hostname or ""
    if not (host.startswith("neverlost-v1-portfolio-") and host.endswith("-neverlost-ai1.vercel.app")):
        raise ValueError("Use the exact immutable protected portfolio preview URL.")
    for index in range(1, 5):
        case_id = f"case_{index:03d}"
        local = execute(case_id)
        start = time.monotonic()
        response = subprocess.run(["node", args.cli, "curl", "/api/v2/run", "--deployment", args.url,
            "--scope", "neverlost-ai1", "--", "--silent", "--show-error", "--fail",
            "-X", "POST", "-H", "Content-Type: application/json", "--data-binary", "@-"],
            input=json.dumps({"case_id": case_id}), text=True, encoding="utf-8",
            capture_output=True, timeout=120)
        if response.returncode:
            raise RuntimeError(f"Protected preview execution failed for {case_id}; exit {response.returncode}")
        remote = json.loads(response.stdout)
        for key in ("artifacts", "reports", "sources", "counts", "result_sha256", "engine"):
            assert local[key] == remote[key], f"{case_id}: V1 {key} differs"
        left, right = copy.deepcopy(local["v1_1"]), copy.deepcopy(remote["v1_1"])
        left.pop("execution")
        right.pop("execution")
        assert left == right, f"{case_id}: V1.1 analytical content differs"
        assert remote["v1_1"]["upstream_v1_sha256"] == remote["result_sha256"]
        print(json.dumps({"case": case_id, "parity": "PASS", "v1": remote["result_sha256"],
            "v11": remote["v1_1"]["result_sha256"], "bytes": len(response.stdout.encode()),
            "cli_roundtrip_seconds": round(time.monotonic() - start, 3),
            "runtime": remote["execution_metrics"], "v11_runtime": remote["v1_1"]["execution"]}), flush=True)


if __name__ == "__main__":
    main()
