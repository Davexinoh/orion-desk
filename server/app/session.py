from __future__ import annotations

import hmac
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import Response

DATA = Path(__file__).resolve().parent.parent / "data" / "sessions.json"
COOKIE = "desk_session"
MAX_AGE = 30 * 24 * 60 * 60


def _secret() -> str:
    return os.getenv("SESSION_SECRET") or "dev-session-secret-change-me"


class SessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, str] = {}
        self.load()

    def load(self) -> None:
        if DATA.exists():
            try:
                self.sessions = json.loads(DATA.read_text(encoding="utf-8")).get("sessions") or {}
            except json.JSONDecodeError:
                self.sessions = {}

    def persist(self) -> None:
        DATA.parent.mkdir(parents=True, exist_ok=True)
        DATA.write_text(json.dumps({"sessions": self.sessions}, indent=2), encoding="utf-8")

    def create(self, user_id: str) -> str:
        sid = uuid4().hex
        self.sessions[sid] = user_id
        self.persist()
        return sign(sid)

    def get_user_id(self, token: str | None) -> str | None:
        sid = unsign(token or "")
        if not sid:
            return None
        return self.sessions.get(sid)

    def destroy(self, token: str | None) -> None:
        sid = unsign(token or "")
        if sid and sid in self.sessions:
            del self.sessions[sid]
            self.persist()


def sign(sid: str) -> str:
    sig = hmac.new(_secret().encode(), sid.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{sid}.{sig}"


def unsign(value: str) -> str | None:
    if "." not in value:
        return None
    sid, sig = value.rsplit(".", 1)
    expected = hmac.new(_secret().encode(), sid.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expected, sig):
        return None
    return sid


def _cookie_flags() -> dict:
    secure = (os.getenv("APP_ORIGIN") or "").startswith("https://")
    return {"httponly": True, "samesite": "lax", "secure": secure, "path": "/"}


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE,
        value=token,
        max_age=MAX_AGE,
        **_cookie_flags(),
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE, **_cookie_flags())


SESSIONS = SessionStore()
