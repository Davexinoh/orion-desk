from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any

import httpx


def verify_telegram_login(payload: dict[str, Any], bot_token: str) -> bool:
    """Telegram Login Widget hash check. Identity only. Does not log the payload."""
    check_hash = str(payload.get("hash") or "")
    if not check_hash or not bot_token:
        return False
    fields: dict[str, str] = {}
    for key, value in payload.items():
        if key == "hash" or value is None or value == "":
            continue
        fields[str(key)] = str(value)
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items(), key=lambda kv: kv[0]))
    secret = hashlib.sha256(bot_token.encode()).digest()
    digest = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, check_hash):
        return False
    try:
        auth_date = int(fields.get("auth_date") or 0)
    except (TypeError, ValueError):
        return False
    if time.time() - auth_date > 300:
        return False
    return True


async def bot_username(bot_token: str) -> str | None:
    if not bot_token:
        return None
    env = os.getenv("TELEGRAM_BOT_USERNAME")
    if env:
        return env.lstrip("@")
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            res = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            data = res.json()
            if data.get("ok"):
                return data["result"].get("username")
    except Exception:
        return None
    return None
