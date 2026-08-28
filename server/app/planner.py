from __future__ import annotations

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

GENERIC_PLAN = [
    {"label": "Understand intent", "tool": None},
    {"label": "Research", "tool": "web.search"},
    {"label": "Draft", "tool": "doc.draft"},
    {"label": "Request approval", "tool": "gmail.send"},
]


def looks_like_acme(intent: str) -> bool:
    t = intent.lower()
    return "acme" in t and "meeting" in t


def plan(intent: str) -> list[dict]:
    raw = ACME_PLAN if looks_like_acme(intent) else GENERIC_PLAN
    steps = [{"label": s["label"], "tool": s["tool"]} for s in raw][:8]
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
