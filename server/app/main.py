from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"
load_dotenv(ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _production() -> bool:
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_ENVIRONMENT_NAME"):
        return True
    return (os.getenv("APP_ORIGIN") or "").startswith("https://")


if _production() and not (os.getenv("SESSION_SECRET") or "").strip():
    raise RuntimeError("SESSION_SECRET is required in production.")

from .auth_email import EMAIL
from .auth_telegram import bot_username, verify_telegram_login
from .approvals import ApprovalError, do_approval, keep_draft, list_needed
from .google_oauth import (
    TOKENS as GOOGLE_TOKENS,
    authorize_url,
    configured as google_configured,
    exchange_code,
    parse_state,
)
from .integrations import payload as integrations_payload
from .events import stream as stream_mission_events
from .mission_store import MISSIONS, PUBLIC_MISSION_IDS
from .runner import run_mission
from .session import COOKIE, SESSIONS, clear_session_cookie, set_session_cookie
from .store import STORE
from .telegram_bot import start_telegram
from .users import USERS

app = FastAPI(title="Orion Desk", version="0.1.0")
_ORIGIN = os.getenv("APP_ORIGIN") or "http://127.0.0.1:5173"
_cors = [_ORIGIN]
if not _production():
    _cors.extend(["http://127.0.0.1:5173", "http://localhost:5173"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_cors)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GoalIn(BaseModel):
    intent: str
    source: str = "web"


class DecisionIn(BaseModel):
    action_id: str


class TelegramLoginIn(BaseModel):
    id: int | str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int | str
    hash: str
    model_config = {"extra": "allow"}


class EmailStartIn(BaseModel):
    email: str
    next: str | None = None


class ProfileIn(BaseModel):
    displayName: str


class MissionIn(BaseModel):
    intent: str


def _session_user(request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        return None
    user = USERS.get(uid)
    if not user:
        return None
    return USERS.public(user)


def _is_local_origin() -> bool:
    origin = (os.getenv("APP_ORIGIN") or "http://127.0.0.1:5173").lower()
    return "127.0.0.1" in origin or "localhost" in origin


def _rotate_session(request: Request, response: Response, user_id: str) -> None:
    SESSIONS.destroy(request.cookies.get(COOKIE))
    set_session_cookie(response, SESSIONS.create(user_id))


def _safe_next(next_path: str | None) -> str:
    if not next_path:
        return "/desk"
    if not next_path.startswith("/desk"):
        return "/desk"
    if next_path.startswith("//") or "://" in next_path:
        return "/desk"
    return next_path


@app.get("/auth/config")
async def auth_config():
    token = os.getenv("TELEGRAM_BOT_TOKEN") or ""
    name = await bot_username(token) if token else None
    return {"telegramBot": name}


@app.get("/auth/me")
def auth_me(request: Request):
    user = _session_user(request)
    if not user:
        raise HTTPException(401, "No session.")
    return {"user": user}


@app.patch("/auth/profile")
def auth_profile(body: ProfileIn, request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    user = USERS.set_display_name(uid, body.displayName)
    if not user:
        raise HTTPException(401, "No session.")
    return {"user": USERS.public(user)}


@app.post("/auth/telegram")
async def auth_telegram(body: TelegramLoginIn, request: Request, response: Response):
    token = os.getenv("TELEGRAM_BOT_TOKEN") or ""
    payload = body.model_dump()
    check = dict(payload)
    if not verify_telegram_login(check, token):
        raise HTTPException(401, "Telegram login failed.")
    link_id = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    user = USERS.upsert_telegram(
        str(body.id),
        body.first_name,
        body.username,
        link_id,
    )
    _rotate_session(request, response, user["id"])
    return {"user": USERS.public(user)}


@app.post("/auth/dev")
def auth_dev(request: Request, response: Response):
    if not _is_local_origin():
        raise HTTPException(404, "Not found.")
    user = USERS.upsert_dev()
    _rotate_session(request, response, user["id"])
    return {"user": USERS.public(user)}


@app.post("/auth/logout")
def auth_logout(request: Request, response: Response):
    SESSIONS.destroy(request.cookies.get(COOKIE))
    clear_session_cookie(response)
    return {"ok": True}


@app.post("/auth/email/start")
def auth_email_start(body: EmailStartIn, request: Request):
    dest = _safe_next(body.next)
    ip = request.client.host if request.client else "unknown"
    try:
        return EMAIL.start(body.email, ip, dest, _is_local_origin())
    except ValueError:
        raise HTTPException(400, "Enter a valid email.")
    except PermissionError:
        raise HTTPException(429, "Could not send the link.")
    except Exception:
        raise HTTPException(500, "Could not send the link.")


@app.get("/auth/email/callback")
def auth_email_callback(request: Request, token: str = ""):
    got = EMAIL.consume(token)
    if not got:
        return RedirectResponse("/sign-in", status_code=302)
    email, dest = got
    link_id = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    user = USERS.upsert_email(email, link_id)
    response = RedirectResponse(_safe_next(dest), status_code=302)
    _rotate_session(request, response, user["id"])
    return response


@app.get("/integrations")
def get_integrations(request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    return integrations_payload(uid)


@app.get("/auth/google/start")
def google_start(request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    if not google_configured():
        return JSONResponse({"ok": False, "reason": "google_not_configured"}, status_code=503)
    return RedirectResponse(authorize_url(uid), status_code=302)


@app.get("/auth/google/callback")
def google_callback(request: Request, code: str = "", state: str = ""):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid or not parse_state(state, uid):
        return RedirectResponse("/desk/settings", status_code=302)
    if not code or not google_configured():
        return RedirectResponse("/desk/settings", status_code=302)
    tokens = exchange_code(code)
    if tokens:
        GOOGLE_TOKENS.save(uid, tokens)
    return RedirectResponse("/desk/settings", status_code=302)


@app.post("/auth/google/disconnect")
def google_disconnect(request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    GOOGLE_TOKENS.delete(uid)
    return {"ok": True}


@app.post("/missions")
def create_mission(body: MissionIn, request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    intent = (body.intent or "").strip()
    if not intent:
        raise HTTPException(400, "Say what you want handled.")
    return run_mission(uid, intent)


@app.get("/missions")
def list_missions(request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    rows = [
        m
        for m in MISSIONS.list_for_user(uid)
        if m.get("id") not in PUBLIC_MISSION_IDS and m.get("userId") == uid
    ]
    return {"missions": rows}


def _mission_or_401(mission_id: str, request: Request) -> dict:
    row = MISSIONS.get(mission_id)
    if not row:
        raise HTTPException(404, "Mission not found.")
    if mission_id not in PUBLIC_MISSION_IDS:
        uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
        if not uid or row.get("userId") != uid:
            raise HTTPException(401, "No session.")
    return row


@app.get("/missions/{mission_id}")
def get_mission(mission_id: str, request: Request):
    return _mission_or_401(mission_id, request)


@app.get("/approvals")
def get_approvals(request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    return {"approvals": list_needed(uid)}


@app.post("/approvals/{approval_id}/do")
def approval_do(approval_id: str, request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    try:
        return do_approval(uid, approval_id)
    except ApprovalError as exc:
        raise HTTPException(exc.status, exc.detail)


@app.post("/approvals/{approval_id}/draft")
def approval_draft(approval_id: str, request: Request):
    uid = SESSIONS.get_user_id(request.cookies.get(COOKIE))
    if not uid:
        raise HTTPException(401, "No session.")
    try:
        return keep_draft(uid, approval_id)
    except ApprovalError as exc:
        raise HTTPException(exc.status, exc.detail)


@app.get("/missions/{mission_id}/events")
async def mission_events(mission_id: str, request: Request):
    row = _mission_or_401(mission_id, request)
    return StreamingResponse(
        stream_mission_events(row),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "agent": "orion-desk",
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "llm": bool(os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY")),
    }


@app.get("/api/state")
def state():
    return STORE.snapshot()


@app.post("/api/goals")
async def create_goal(body: GoalIn):
    raise HTTPException(410, "Gone. Use POST /missions.")


@app.get("/api/goals/{gid}")
def get_goal(gid: str):
    raise HTTPException(410, "Gone. Use GET /missions/{id}.")


@app.get("/api/goals/{gid}/stream")
async def stream_goal(gid: str):
    raise HTTPException(410, "Gone. Use GET /missions/{id}/events.")


@app.get("/api/receipts")
def receipts():
    raise HTTPException(410, "Gone.")


@app.get("/api/receipts/{rid}/text")
def receipt_text(rid: str):
    raise HTTPException(410, "Gone.")


@app.post("/api/receipts/{rid}/approve")
async def approve(rid: str, body: DecisionIn):
    raise HTTPException(410, "Gone. Use POST /approvals/{id}/do.")


@app.post("/api/receipts/{rid}/decline")
async def decline(rid: str, body: DecisionIn):
    raise HTTPException(410, "Gone. Use POST /approvals/{id}/draft.")


@app.get("/api/memory")
def memory():
    return STORE.snapshot()["memory"]


@app.get("/api/integrations")
def integrations():
    snap = STORE.snapshot()["integrations"]
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        for i in snap:
            if i["id"] == "telegram":
                i["connected"] = True
                i["status"] = "Bot is live."
    return snap


@app.on_event("startup")
async def _startup():
    await start_telegram()


def _mount_web() -> None:
    if not WEB_DIST.is_dir():
        return
    assets = WEB_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path:
            candidate = (WEB_DIST / full_path).resolve()
            try:
                candidate.relative_to(WEB_DIST.resolve())
            except ValueError:
                raise HTTPException(404, "Not found.")
            if candidate.is_file():
                return FileResponse(candidate)
        index = WEB_DIST / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(404, "Not found.")


_mount_web()
