from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

import httpx

DATA = Path(__file__).resolve().parent.parent / "data" / "google_tokens.json"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def _secret() -> str:
    return os.getenv("SESSION_SECRET") or "dev-session-secret-change-me"


def client_id() -> str:
    return (os.getenv("GOOGLE_CLIENT_ID") or "").strip()


def client_secret() -> str:
    return (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()


def redirect_uri() -> str:
    return (os.getenv("GOOGLE_REDIRECT_URI") or "").strip()


def configured() -> bool:
    return bool(client_id() and client_secret() and redirect_uri())


def make_state(user_id: str) -> str:
    nonce = uuid4().hex
    exp = str(int(time.time()) + 600)
    payload = f"{user_id}.{nonce}.{exp}"
    sig = hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"


def parse_state(state: str, user_id: str) -> bool:
    if state.count(".") < 3:
        return False
    user, nonce, exp, sig = state.rsplit(".", 3)
    if user != user_id or not nonce or not exp:
        return False
    try:
        if int(exp) < int(time.time()):
            return False
    except ValueError:
        return False
    payload = f"{user}.{nonce}.{exp}"
    expected = hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(expected, sig)


def authorize_url(user_id: str) -> str:
    params = {
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": make_state(user_id),
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict[str, Any] | None:
    try:
        with httpx.Client(timeout=12) as client:
            res = client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": client_id(),
                    "client_secret": client_secret(),
                    "redirect_uri": redirect_uri(),
                },
            )
            if res.status_code >= 400:
                return None
            data = res.json()
    except Exception:
        return None
    access = data.get("access_token")
    if not access:
        return None
    expires_in = int(data.get("expires_in") or 3600)
    scopes = data.get("scope") or " ".join(SCOPES)
    if isinstance(scopes, str):
        scope_list = scopes.split()
    else:
        scope_list = list(scopes)
    return {
        "access_token": access,
        "refresh_token": data.get("refresh_token"),
        "expiry": int(time.time()) + expires_in,
        "scopes": scope_list,
    }


class TokenStore:
    def __init__(self) -> None:
        self.by_user: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if not DATA.exists():
            return
        try:
            raw = json.loads(DATA.read_text(encoding="utf-8"))
            self.by_user = raw.get("users") or {}
        except json.JSONDecodeError:
            self.by_user = {}

    def persist(self) -> None:
        DATA.parent.mkdir(parents=True, exist_ok=True)
        DATA.write_text(json.dumps({"users": self.by_user}, indent=2), encoding="utf-8")

    def get(self, user_id: str) -> dict[str, Any] | None:
        return self.by_user.get(user_id)

    def connected(self, user_id: str | None) -> bool:
        if not user_id:
            return False
        row = self.get(user_id)
        return bool(row and row.get("access_token"))

    def save(self, user_id: str, tokens: dict[str, Any]) -> None:
        prev = self.by_user.get(user_id) or {}
        refresh = tokens.get("refresh_token") or prev.get("refresh_token")
        self.by_user[user_id] = {
            "access_token": tokens["access_token"],
            "refresh_token": refresh,
            "expiry": tokens["expiry"],
            "scopes": tokens.get("scopes") or prev.get("scopes") or [],
        }
        self.persist()

    def delete(self, user_id: str) -> None:
        if user_id in self.by_user:
            del self.by_user[user_id]
            self.persist()


TOKENS = TokenStore()


def access_token(user_id: str | None) -> str | None:
    if not user_id:
        return None
    row = TOKENS.get(user_id)
    if not row or not row.get("access_token"):
        return None
    expiry = int(row.get("expiry") or 0)
    if expiry and expiry < int(time.time()) + 30:
        refreshed = _refresh(user_id)
        if refreshed:
            return refreshed
    return str(row["access_token"])


def _refresh(user_id: str) -> str | None:
    row = TOKENS.get(user_id)
    if not row or not row.get("refresh_token") or not configured():
        return None
    try:
        with httpx.Client(timeout=12) as client:
            res = client.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": row["refresh_token"],
                    "client_id": client_id(),
                    "client_secret": client_secret(),
                },
            )
            if res.status_code >= 400:
                return None
            data = res.json()
    except Exception:
        return None
    access = data.get("access_token")
    if not access:
        return None
    expires_in = int(data.get("expires_in") or 3600)
    TOKENS.save(
        user_id,
        {
            "access_token": access,
            "refresh_token": data.get("refresh_token") or row.get("refresh_token"),
            "expiry": int(time.time()) + expires_in,
            "scopes": row.get("scopes") or [],
        },
    )
    return str(access)


def google_post(
    user_id: str, url: str, json_body: dict | None = None
) -> httpx.Response | None:
    token = access_token(user_id)
    if not token:
        return None
    try:
        with httpx.Client(timeout=12) as client:
            res = client.post(
                url, json=json_body, headers={"Authorization": f"Bearer {token}"}
            )
            if res.status_code == 401:
                token = _refresh(user_id)
                if not token:
                    return res
                res = client.post(
                    url, json=json_body, headers={"Authorization": f"Bearer {token}"}
                )
            return res
    except Exception:
        return None


def google_get(user_id: str, url: str, params: dict | None = None) -> httpx.Response | None:
    token = access_token(user_id)
    if not token:
        return None
    try:
        with httpx.Client(timeout=12) as client:
            res = client.get(url, params=params, headers={"Authorization": f"Bearer {token}"})
            if res.status_code == 401:
                token = _refresh(user_id)
                if not token:
                    return res
                res = client.get(url, params=params, headers={"Authorization": f"Bearer {token}"})
            return res
    except Exception:
        return None

