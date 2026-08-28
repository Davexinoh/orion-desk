from __future__ import annotations

import re

from .tools_mock import ALLOW, GATED

ACME_PLAN = [
    {"label": "Calendar inspected", "tool": "calendar.read"},
    {"label": "Email history analyzed", "tool": "gmail.search"},
    {"label": "Documents retrieved", "tool": "drive.read"},
    {"label": "External research completed", "tool": "web.search"},
    {"label": "Meeting briefing generated", "tool": "doc.draft"},
    {"label": "Preparation block scheduled", "tool": "doc.draft"},
    {"label": "Follow-up drafted", "tool": "doc.draft"},
    {"label": "Send agenda to attendees", "tool": "gmail.send"},
]

_MEETING_RE = re.compile(
    r"\b(meetings?|calls?|standup|stand-up|agenda)\b",
    re.IGNORECASE,
)
_SEND_RE = re.compile(
    r"\b(send|invite|share)\b|\be-?mail(s|ed|ing)?\s+(this|it|to|them|her|him)\b",
    re.IGNORECASE,
)
_CAL_RE = re.compile(
    r"\b(calendar|tomorrow|today|tonight|event|schedule|o'?clock)\b|"
    r"\b\d{1,2}\s*(am|pm)\b|\bat\s+\d{1,2}\b",
    re.IGNORECASE,
)


def looks_like_meeting(intent: str) -> bool:
    return bool(_MEETING_RE.search(intent or ""))


def looks_like_send(intent: str) -> bool:
    return bool(_SEND_RE.search(intent or ""))


def looks_like_calendar(intent: str) -> bool:
    return bool(_CAL_RE.search(intent or ""))


def looks_like_acme(intent: str) -> bool:
    t = (intent or "").lower()
    return "acme" in t and looks_like_meeting(intent)


def _meeting_plan(intent: str) -> list[dict]:
    steps = [dict(s) for s in ACME_PLAN]
    if not looks_like_calendar(intent):
        steps = [s for s in steps if s.get("tool") != "calendar.read"]
    if not looks_like_send(intent):
        steps = [s for s in steps if s.get("tool") not in GATED]
    return steps


def _generic_plan(intent: str) -> list[dict]:
    t = (intent or "").lower()
    steps: list[dict] = [{"label": "Understand outcome", "tool": None}]
    mail = any(w in t for w in ("inbox", "mail", "email", "thread", "waiting on me"))
    files = any(w in t for w in ("notes", "doc", "drive", "file", "pdf"))
    web = any(w in t for w in ("research", "web", "search", "company", "news", "recipe"))
    if looks_like_calendar(intent):
        steps.append({"label": "Calendar inspected", "tool": "calendar.read"})
    if mail:
        steps.append({"label": "Gather mail context", "tool": "gmail.search"})
    if files:
        steps.append({"label": "Gather files", "tool": "drive.read"})
    if web or not (mail or files or looks_like_calendar(intent)):
        steps.append({"label": "Gather context", "tool": "web.search"})
    steps.append({"label": "Draft the artifact", "tool": "doc.draft"})
    if looks_like_send(intent):
        steps.append({"label": "Ask before send", "tool": "gmail.send"})
    if len(steps) > 6:
        tail = [s for s in steps if s.get("tool") in GATED]
        head = [s for s in steps if s.get("tool") not in GATED][: 6 - len(tail)]
        steps = head + tail
    return steps


def plan(intent: str) -> list[dict]:
    raw = _meeting_plan(intent) if looks_like_meeting(intent) else _generic_plan(intent)
    cap = 8 if looks_like_meeting(intent) else 6
    steps = [{"label": s["label"], "tool": s["tool"]} for s in raw][:cap]
    if looks_like_send(intent) and steps and steps[-1].get("tool") not in GATED:
        steps = steps[: cap - 1] + [{"label": "Ask before send", "tool": "gmail.send"}]
    if not _valid(steps):
        return [{"label": "Could not plan this", "tool": None, "failed": True}]
    return steps


def _valid(steps: list[dict]) -> bool:
    if not steps or len(steps) > 8:
        return False
    for i, step in enumerate(steps):
        tool = step.get("tool")
        if tool is None:
            continue
        if tool not in ALLOW:
            return False
        if tool == "gmail.send" and i != len(steps) - 1:
            return False
        if tool in GATED and i != len(steps) - 1:
            return False
    return True
