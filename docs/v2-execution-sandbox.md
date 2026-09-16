# V2 execution sandbox — first execution gate

New V2 integration, not historical code. Work branch: `v2-live-app`. The historical V1/V1.1 portfolio routes remain unchanged. Case Navigator, Full Human Pathway, Neverlost OS, accepted-state behavior, real records, uploads and durable storage are outside this gate.

## Source custody

`engine/recovery-manifest.json` records the SHA-256 of all 25 frozen public V1 source/schema/dependency files. They are copied byte-for-byte under `engine/historical/v1` and protected from Git line-ending conversion. The original publication repository and active recovered workspaces are not edited.

The active recovered V1.1 workspace was located and compared read-only. Its dependency file and 21 source/schema files match V1; three modules are modified and three are added. The manifest records each comparison and the six delta hashes. The active copy contains identifying patterns and private batch assumptions. None of those six modules, private configurations, records or outputs has been copied here. They are **recovered, not imported**, not missing and not replaced silently with TypeScript fixtures. V1.1 live processing is not integrated at this gate.

The V1.1 final-synthesis generator remains unrecovered. File comparison supports a direct code extension, not authenticated Git ancestry. Existing ordinary V1 reports are not evidence of a V1.1 final-packet generator.

## Actual execution

`engine/runtime/adapter.py` verifies the engine and synthetic document hashes, then creates a unique temporary directory for each request. Byte-identical source files run in a fresh Python subprocess with their original relative `data/` and `outputs/` layout **inside that directory**. This relocates the complete historical filesystem root rather than patching imported global constants in a shared process.

No profile is copied: the original generic profile fallback applies. Child environment variables are restricted to operating-system execution needs; application secrets are not inherited. The historical `main.py` runs extraction, chunking, events, timeline, evidence matrix, hidden states, trust thresholds, bottlenecks, capacity windows, and ordinary Markdown reports. JSON and Markdown are read from the generated files; no prepared analytical JSON is substituted.

Cleanup runs on both success and failure. A subprocess timeout is 45 seconds. Public errors omit stderr and local paths. A process-local two-execution semaphore bounds work per API instance; it is not distributed rate limiting or a production abuse-control system.

## Synthetic-only boundary

Three independently invented scenarios use Markdown, TXT and a single-page text-bearing PDF. Each document has an ID, filename, synthetic flag, declared source type, expected page/text-record count, description, fixture version and SHA-256. Manifest source types are fixture declarations, not authenticated authorship.

The HTTP request accepts exactly `{"case_id":"case_001"}` (or another allowlisted ID). Text, paths, profiles and uploads are rejected. The backend checks content hashes and rejects PDFs that require OCR. The untouched Windows OCR helper is preserved as evidence but is not a supported web OCR engine. Adding a Linux OCR engine would be a separately documented V2 adaptation.

## API and ephemeral state

- `GET /api/v2/cases`: approved manifest.
- `GET /api/v2/cases/{case_id}`: one approved case.
- `POST /api/v2/run`: synchronous real Python execution, generated outputs and run ledger.
- `GET /api/v2/run/{run_id}`: HTTP 410 with an explicit no-durable-storage explanation.

Responses have no-store headers. The UI keeps the current result only in React memory across V2 navigation. Direct entry and refresh work, but present an honest empty-run state requiring re-execution. No localStorage, sessionStorage, database, upload storage or cross-instance run lookup is implied. Durable refresh restoration is a later persistence gate.

The ledger separates historical V1 engine hash, new runtime version, source hashes, result digest and execution timestamps. The deterministic result digest excludes run IDs and timestamps. Dependencies are pinned separately from the original historical requirements.

These runtime dependency pins are new V2 choices satisfying the recovered requirements, not an authenticated June dependency lock. Local/preview parity verifies this execution environment; it does not establish reproduction of unavailable private historical outputs.

## Historical limitations preserved

- `not approved` can produce a historical **Barrier removed** candidate. The regression asserts preservation of that defect and an explicit warning, not correctness.
- Event classification chooses one keyword-scored type for a chunk. A therapy paragraph can be classified as a functional limitation and consequently generate no capacity window. Empty output remains empty.
- Event summaries/source excerpts are truncated by the historical code (normally 420 characters). Appending text beyond that point can change the extracted source without changing the evidence matrix. The same-document regression changes substantive wording within the retained span; it does not claim every edit affects every downstream artifact.
- Report templates can make broader statements than the inputs establish. They are shown verbatim as draft historical output with visible limitations, not verified conclusions.
- Event IDs derive from chunk identifiers, not content-integrity hashes. V2 document/result hashes are newly introduced integrity metadata, not historical provenance.
- Exact document/chunk inspection is enabled only when the returned references resolve. Other historical source lists remain visible as raw generated fields; no stronger linkage is fabricated.
- Reports retain historical “AI/rule-based” wording. No LLM executes; the historical interface is disabled.

## Local use

Create an ignored virtual environment and install `requirements-test.txt`:

```powershell
python -m venv engine/.venv
engine/.venv/Scripts/python.exe -m pip install -r requirements-test.txt
engine/.venv/Scripts/python.exe -B -m engine.runtime.runner case_001
engine/.venv/Scripts/python.exe -B -m uvicorn api.index:app --host 127.0.0.1 --port 8100 --no-access-log
```

In another terminal run `npm run dev`, then open `/v2`. On Unix use `engine/.venv/bin/python`. Next.js proxies only the V2 API namespace locally. Existing V1/V1.1 routes remain fixture-backed historical presentations.

## Verification commands

```powershell
engine/.venv/Scripts/python.exe -B -m unittest discover -s tests/v2 -v
python -B -m unittest discover -s ../publication/neverlost-v1/tests -v
npm run lint
npm run typecheck
npm run build
npm run test:e2e
git diff --check
```

Playwright starts the local Python service and production Next.js server. V2 tests execute real Python, cover all output views, inspect PDF provenance by keyboard, exercise failure without fixture fallback, check refresh/direct entry, and run desktop/mobile WCAG checks. The five original recovery tests remain outside this repository and are run without edits.

## Deployment gate

The first remote run exposed a Vercel packaging difference: dependencies are vendored via Python's search path, outside the child interpreter's default site-packages. The adapter now supplies only the resolved installation roots of pypdf, Pillow and PyYAML to the child process. It does not inherit arbitrary `PYTHONPATH` or application secrets. This is a V2 runtime adaptation, not an analytical change; a regression checks the environment boundary.

Preview only; do not merge or publish production. `vercel.json` routes the V2 namespace to the Python function while retaining Next.js for the interface. The upload allowlist includes only the application, public-safe engine and curated sources; it excludes the virtual environment, bytecode, local configuration and secrets.

Before calling this milestone complete, verify the preview actually executes Python and compare its deterministic result digest to the local run for every case. A successful Next.js build alone does not establish this. V1.1 live processing, persistence and private-document architecture remain separate later gates.

## Verified preview — September 16, 2026

- Preview deployment `dpl_HktiW7KCnWiLhtNhu68zTaypYBwE` is READY: https://neverlost-v1-portfolio-8jk6kzoud-neverlost-ai1.vercel.app/v2
- Source is the uncommitted `v2-live-app` worktree based on `b735423d627f2087d43fa390b784c7bbb3ab5ef0`; no commit, push, main merge or production promotion was performed.
- Real remote Python executions for all three cases match local SHA-256 result digests exactly:
  - `case_001`: `2fe0a970dad56556b17c013c58636e14fc4731a1f4aae864da6a05c303bec27f`
  - `case_002`: `367773e04b8f76d8057a9a9b983147371b0e1d7255bc9ff388033dde02f0cd9a`
  - `case_003`: `b9ad3137bd3ca42298a3f57603b3c43b33f6413de93d5466e965a86b7f70c838`
- 20 Python runtime/API tests and five original frozen V1 recovery tests pass. All 25 historical hashes remain unchanged.
- Full desktop/mobile Playwright suite: 96 passed before the dependency-path adapter fix. After the fix, all four focused V2 desktop/mobile tests passed again, alongside the Python environment-isolation regression and remote desktop/mobile execution checks.
- Protected-preview desktop/mobile smoke passed across all seven result surfaces, with source inspection, Escape dismissal, refresh-to-empty behavior, no page errors or horizontal overflow, and no WCAG A/AA violations in the scoped scans. Preview protection remains enabled; the CLI-issued browser cookie was temporary and excluded from Git/deployment.
- Lint, TypeScript, local production build, remote production-mode build and whitespace checks pass. Existing tracked V1/V1.1 interface files remain unchanged.
- Production remains `dpl_8PAv6azHxfRYukG2n2uWGQF3SLTQ`; `main` remains the original base commit.

Non-blocking tooling warnings: existing ESLint 10 peer-range warnings from Next's plugins, an npm install-script approval notice for `unrs-resolver`, and a test-only Starlette/httpx deprecation notice. Installation reported zero audited npm vulnerabilities; these checks are not a comprehensive security certification. Public abuse controls, real-document privacy architecture, durable persistence and V1.1 integration remain later gates.
