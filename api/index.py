"""Synthetic-only V2 API. No upload, external AI, or durable case state."""
import json
from threading import BoundedSemaphore

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from engine.runtime.adapter import ExecutionFailed, InputRejected, case_detail, cases, execute

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
slots = BoundedSemaphore(2)


@app.middleware("http")
async def safe_boundary(request: Request, call_next):
    # Vercel rewrite routes to one Python function; local ASGI uses the same path.
    forwarded = request.query_params.get("v2_path")
    if forwarded is not None:
        request.scope["path"] = "/api/v2/" + forwarded.strip("/")
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/api/v2/cases")
def list_cases():
    return {"cases": cases()}


@app.get("/api/v2/cases/{case_id}")
def get_case(case_id: str):
    try:
        return case_detail(case_id)
    except InputRejected as error:
        return JSONResponse({"error": str(error)}, status_code=404)


@app.post("/api/v2/run")
async def run(request: Request):
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        return JSONResponse({"error": "Only an approved synthetic case ID is accepted."}, status_code=415)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 256:
            return JSONResponse({"error": "Request exceeds the case-selection limit."}, status_code=413)
    try:
        selection = json.loads(body)
        if (not isinstance(selection, dict) or set(selection) != {"case_id"}
                or not isinstance(selection["case_id"], str)):
            raise ValueError
        case_detail(selection["case_id"])
    except (ValueError, UnicodeError):
        return JSONResponse({"error": "Choose one approved synthetic case ID. No documents or paths are accepted."}, status_code=400)
    if not slots.acquire(blocking=False):
        return JSONResponse({"error": "Execution capacity reached. Try again shortly."}, status_code=429)
    try:
        result = await run_in_threadpool(execute, selection["case_id"])
        return JSONResponse(result)
    except InputRejected as error:
        return JSONResponse({"error": str(error)}, status_code=400)
    except ExecutionFailed as error:
        return JSONResponse({"error": str(error)}, status_code=503)
    except Exception:
        # Never expose local paths, subprocess stderr, or request text.
        return JSONResponse({"error": "Analysis failed. No fixture result was substituted."}, status_code=503)
    finally:
        slots.release()


@app.get("/api/v2/run/{run_id}")
def get_run(run_id: str):
    return JSONResponse({"error": "Runs are not durably stored in this execution proof. Run an approved case again."}, status_code=410)
