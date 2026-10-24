"""Server-side auth for the lab.

Google sign-in is verified on the server: the ID token the browser received
from Google is checked against Google's tokeninfo endpoint (audience must be
this app's OAuth client id, issuer must be Google, token must be unexpired).
A verified user gets a short-lived HMAC session token for this API; writes
require it. Reads stay public so share links work without a login.

Rate limits are a best-effort per-process guard (serverless instances each
hold their own counters) — they stop casual abuse, not a determined flood.
"""
import base64
import hashlib
import hmac
import json
import time
from collections import defaultdict, deque

import httpx
from fastapi import Header, HTTPException

from app.config import settings

SESSION_TTL_SECONDS = 7 * 24 * 3600


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def make_session(email: str, name: str = "", picture: str = "") -> str:
    payload = {"email": email, "name": name, "picture": picture,
               "exp": int(time.time()) + SESSION_TTL_SECONDS}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(settings.session_secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(sig)}"


def verify_session(token: str) -> dict | None:
    try:
        body, sig = token.split(".", 1)
        expect = hmac.new(settings.session_secret.encode(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expect, _unb64(sig)):
            return None
        payload = json.loads(_unb64(body))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def require_user(authorization: str | None = Header(default=None)) -> dict:
    """Dependency for write endpoints. Missing/invalid session -> 401."""
    if authorization and authorization.startswith("Bearer "):
        payload = verify_session(authorization[7:].strip())
        if payload:
            return payload
    raise HTTPException(
        status_code=401,
        detail={"code": "auth_required", "message": "Sign in with Google first (the lab's Sign in page)."},
    )


def optional_user(authorization: str | None = Header(default=None)) -> dict | None:
    if authorization and authorization.startswith("Bearer "):
        return verify_session(authorization[7:].strip())
    return None


def verify_google_credential(credential: str) -> dict:
    """Validate a Google ID token server-side via tokeninfo."""
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential},
            )
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"code": "google_unreachable", "message": f"Could not reach Google: {exc}"})
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail={"code": "bad_google_token", "message": "Google token invalid or expired. Sign in again."})
    info = resp.json()
    if info.get("aud") != settings.google_client_id:
        raise HTTPException(status_code=401, detail={"code": "bad_audience", "message": "Token was not issued for this app."})
    if info.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
        raise HTTPException(status_code=401, detail={"code": "bad_issuer", "message": "Token issuer is not Google."})
    if int(info.get("exp", 0)) < time.time():
        raise HTTPException(status_code=401, detail={"code": "token_expired", "message": "Google token expired. Sign in again."})
    return {"email": info.get("email", ""), "name": info.get("name", ""),
            "picture": info.get("picture", "")}


# --- simple per-process rate limits -----------------------------------------
_WINDOWS: dict[str, deque] = defaultdict(deque)


def rate_limit(key: str, limit: int, window_seconds: int = 60) -> None:
    now = time.time()
    q = _WINDOWS[key]
    while q and q[0] <= now - window_seconds:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(
            status_code=429,
            detail={"code": "rate_limited", "message": f"Too many requests — limit is {limit} per minute. Slow down."},
        )
    q.append(now)


def rate_limit_run(ip: str, llm: bool = False) -> None:
    # LLM runs cost real provider money, so they get a tighter budget.
    rate_limit(f"run:{ip}", 10 if llm else 60)
