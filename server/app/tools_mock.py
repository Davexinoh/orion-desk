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
    from .tools_google import gmail_search_live, has_grant

    if has_grant(user_id) and user_id:
        return gmail_search_live(intent, user_id)
    if _is_acme(intent):
        return {"ok": True, "evidence": "6 previous emails read", "mode": "mock"}
    return {"ok": True, "evidence": "Related threads listed.", "mode": "mock"}


def drive_read(intent: str, user_id: str | None = None, **_: Any) -> dict[str, Any]:
    from .tools_google import drive_read_live, has_grant

    if has_grant(user_id) and user_id:
        return drive_read_live(intent, user_id)
    if _is_acme(intent):
        return {"ok": True, "evidence": "2 relevant documents reviewed", "mode": "mock"}
    return {"ok": True, "evidence": "Relevant files listed.", "mode": "mock"}


def web_search_key() -> str:
    return (os.getenv("TAVILY_API_KEY") or "").strip()


def web_search(intent: str, **_: Any) -> dict[str, Any]:
    key = web_search_key()
    if key:
        live = _web_search_live(intent, key)
        live.setdefault("mode", "live")
        if live.get("ok"):
            return live
    return _web_search_mock(intent)


def _web_search_mock(intent: str) -> dict[str, Any]:
    if _is_acme(intent):
        return {"ok": True, "evidence": "Company researched", "mode": "mock"}
    return {"ok": True, "evidence": "Sources listed.", "mode": "mock"}


def _search_query(intent: str) -> str:
    q = " ".join((intent or "").split())
    q = re.sub(
        r"^(need|i need|please|can you|help me|i want|i'd like)\s+",
        "",
        q,
        flags=re.I,
    )
    return q[:120] or "research"


def _web_search_live(intent: str, key: str) -> dict[str, Any]:
    query = _search_query(intent)
    try:
        with httpx.Client(timeout=8.0) as client:
            res = client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3,
                    "include_answer": False,
                },
            )
            res.raise_for_status()
            data = res.json()
    except Exception:
        return {"ok": False, "evidence": "Web search failed.", "mode": "live"}
    titles = [
        str(item.get("title") or "").strip()
        for item in (data.get("results") or [])
        if isinstance(item, dict)
    ]
    titles = [t for t in titles if t][:3]
    topic = query[:48] if query else "topic"
    if not titles:
        return {"ok": True, "evidence": f"Tavily: 0 sources on {topic}", "mode": "live"}
    evidence = f"Tavily: {len(titles)} sources on {topic} — " + "; ".join(titles)
    return {"ok": True, "evidence": _one_line(evidence, 160), "mode": "live"}


def _one_line(text: str, limit: int = 80) -> str:
    line = " ".join(text.split())
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip() + "…"


def doc_draft(
    intent: str,
    label: str = "",
    prior_evidence: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    from .tools_draft import doc_draft_live, llm_configured

    if llm_configured():
        return doc_draft_live(intent, label, prior_evidence)
    kind, title, body = _draft_body(intent, label)
    if prior_evidence and not _is_acme(intent):
        body = _draft_from_evidence(kind, intent, prior_evidence, body)
    return {
        "ok": True,
        "evidence": "Draft written. Not sent.",
        "artifact": {"kind": kind, "title": title, "body": body},
        "mode": "mock",
    }


def _draft_from_evidence(kind: str, intent: str, prior: list[str], fallback: str) -> str:
    notes = "\n".join(f"- {p}" for p in prior[:8] if p)
    if not notes:
        return fallback
    return f"{kind}\n{intent}\n\n{notes}\n"


def calendar_write(*, approval_id: str | None = None, **_: Any) -> dict[str, Any]:
    global calendar_write_called
    calendar_write_called = True
    if not approval_id:
        return {"ok": False, "evidence": "Needs approval.", "gated": True, "mode": "mock"}
    return {
        "ok": False,
        "evidence": "Calendar is not connected.",
        "gated": True,
        "mode": "mock",
    }


def gmail_send(*, approval_id: str | None = None, **_: Any) -> dict[str, Any]:
    global gmail_send_called
    gmail_send_called = True
    if not approval_id:
        return {"ok": False, "evidence": "Needs approval.", "gated": True, "mode": "mock"}
    return {
        "ok": False,
        "evidence": "Gmail is not connected.",
        "gated": True,
        "mode": "mock",
    }


def drive_share(*, approval_id: str | None = None, **_: Any) -> dict[str, Any]:
    if not approval_id:
        return {"ok": False, "evidence": "Needs approval.", "gated": True, "mode": "mock"}
    return {"ok": True, "evidence": "Share recorded.", "gated": True, "mode": "mock"}


ADAPTERS = {
    "calendar.read": calendar_read,
    "gmail.search": gmail_search,
    "drive.read": drive_read,
    "web.search": web_search,
    "doc.draft": doc_draft,
    "calendar.write": calendar_write,
    "gmail.send": gmail_send,
    "drive.share": drive_share,
}

TOOL_LABELS = {
    "calendar.read": "Calendar",
    "gmail.search": "Gmail",
    "drive.read": "Drive",
    "web.search": "Web",
    "doc.draft": "Draft",
    "calendar.write": "Calendar",
    "gmail.send": "Gmail",
    "drive.share": "Drive",
}


_MEETING_RE = re.compile(
    r"\b(meetings?|calls?|standup|stand-up|agenda)\b",
    re.IGNORECASE,
)


def _is_meeting(intent: str) -> bool:
    return bool(_MEETING_RE.search(intent or ""))


def _is_acme(intent: str) -> bool:
    t = (intent or "").lower()
    return "acme" in t and _is_meeting(intent)


def _draft_body(intent: str, label: str) -> tuple[str, str, str]:
    low = (label or "").lower()
    want = (intent or "").lower()
    if _is_acme(intent):
        if "brief" in low:
            return (
                "brief",
                "Acme brief",
                "Acme — tomorrow 14:00\nJane, Mark, Priya, Dan\n\n"
                "They are deciding the 200-seat expansion. Proposal v3 is current. "
                "Open: pricing, unsigned DPA, SOC 2, pilot end date.\n\n"
                "Lead with the pricing table. Do not reopen scope.",
            )
        if "follow" in low:
            return (
                "followUp",
                "Follow-up",
                "Subject: Recap — Acme expansion review\n\n"
                "Jane, Mark, Priya, Dan —\n\n"
                "Notes from today, then owners.\n\n"
                "Not sent.",
            )
        if "prep" in low or "block" in low or "calendar" in low:
            return ("calendar", "Prep block", "Prep block tomorrow 13:15–13:45")
        return (
            "agenda",
            "Agenda — Acme, tomorrow 2:00 PM",
            "Agenda — Acme, tomorrow 2:00 PM\n\n"
            "1. Pilot status\n"
            "2. Open commercial points\n"
            "3. Legal / DPA / SOC 2\n"
            "4. Pilot end date\n"
            "5. Owners and next steps\n\n"
            "Not sent.",
        )
    if _is_meeting(intent):
        if "follow" in low:
            return ("followUp", "Follow-up", f"Draft follow-up for:\n{intent}\n\nNot sent.")
        if "prep" in low or "block" in low or "calendar" in low:
            return ("calendar", "Prep block", "Prep block proposed. Not written.")
        if "brief" in low:
            return ("brief", "Brief", f"Brief for:\n{intent}")
        return ("agenda", "Draft", f"Draft for:\n{intent}\n\nNot sent.")
    if any(w in want for w in ("recipe", "cook", "dinner", "menu")):
        return (
            "recipe",
            "Recipe",
            f"Recipe for two\n\n{intent}\n\nIngredients and steps go here.\n",
        )
    if (
        "waiting on me" in want
        or "inbox" in want
        or "list" in low
        or "task" in want
        or "what is waiting" in low
    ):
        return ("list", "Waiting list", f"Waiting on you\n\n{intent}\n")
    if "email" in low or "mail" in want:
        return ("email", "Email", f"Draft email for:\n{intent}\n\nNot sent.")
    if "brief" in low:
        return ("brief", "Brief", f"Brief for:\n{intent}")
    if "follow" in low:
        return ("followUp", "Follow-up", f"Draft follow-up for:\n{intent}\n\nNot sent.")
    return ("doc", "Draft", f"{intent}\n")
