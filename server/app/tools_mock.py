from __future__ import annotations

import os
import re
from typing import Any

import httpx

AUTO = frozenset(
    {"calendar.read", "gmail.search", "drive.read", "web.search", "doc.draft"}
)
GATED = frozenset({"gmail.send", "calendar.write", "drive.share"})
ALLOW = AUTO | GATED

gmail_send_called = False
calendar_write_called = False


def reset_call_flags() -> None:
    global gmail_send_called, calendar_write_called
    gmail_send_called = False
    calendar_write_called = False


def calendar_read(intent: str, user_id: str | None = None, **_: Any) -> dict[str, Any]:
    from .tools_google import calendar_read_live, has_grant

    if has_grant(user_id) and user_id:
        return calendar_read_live(intent, user_id)
    return {
        "ok": True,
        "evidence": "Calendar is not connected; using stated time.",
        "mode": "mock",
    }


def gmail_search(intent: str, user_id: str | None = None, **_: Any) -> dict[str, Any]:
   
