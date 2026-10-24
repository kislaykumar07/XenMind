"""Vercel entrypoint: statically defines `app` (required by Vercel's FastAPI
detection) and lazily delegates every request to the real XenMind backend app
(api/app/main.py). If the real app fails to import in the serverless runtime,
the traceback is returned as JSON instead of a silent 500."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import JSONResponse, Response  # noqa: E402

app = FastAPI()
_state = {}


def _load_real():
    if "real" not in _state and "err" not in _state:
        try:
            from app.main import app as real_app

            _state["real"] = real_app
        except Exception:
            _state["err"] = traceback.format_exc()
    return _state.get("real")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def _proxy(path: str, request: Request):
    real = _load_real()
    if real is None:
        return JSONResponse({"status": "import_failed", "error": _state["err"]}, status_code=200)
    if path.startswith("api/index.py"):
        path = path[len("api/index.py"):].lstrip("/")
    import httpx

    transport = httpx.ASGITransport(app=real)
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    async with httpx.AsyncClient(transport=transport, base_url="http://internal") as client:
        resp = await client.request(
            request.method, "/" + path, params=dict(request.query_params), headers=headers, content=body
        )
    out_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in ("content-length", "transfer-encoding")
    }
    return Response(
        content=resp.content, status_code=resp.status_code, headers=out_headers,
        media_type=resp.headers.get("content-type"),
    )
