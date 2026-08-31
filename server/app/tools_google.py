from __future__ import annotations

import base64
import re
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any

from .google_oauth import TOKENS, google_get, google_post


def calendar_read_live(intent: str, user_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    time_min = now.isoformat().replace("+00:00", "Z")
    time_max = (now + timedelta(days=7)).isoformat().replace("+00:00", "Z")
    q = _search_query(intent)
    res = google_get(
        user_id,
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": "5",
            "q": q,
        },
    )
    if res is None or res.status_code >= 400:
        return {
            "ok": True,
            "evidence": "Calendar is not connected; using stated time.",
            "mode": "mock" if res is None else "live",
        }
    items = (res.json() or {}).get("items") or []
    if not items:
        return {
            "ok": True,
            "evidence": "No event matched; using stated time.",
            "mode": "live",
        }
    ev = items[0]
    summary = str(ev.get("summary") or "Event").strip() or "Event"
    when = _event_when(ev.get("start") or {})
    return {
        "ok": True,
        "evidence": _one_line(f"Found event: {summary} / {when}"),
        "mode": "live",
    }


def gmail_search_live(intent: str, user_id: str) -> dict[str, Any]:
    q = _gmail_query(intent)
    res = google_get(
        user_id,
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        {"q": q, "maxResults": "8"},
    )
    if res is None or res.status_code >= 400:
        return {
            "ok": True,
            "evidence": "No mail context; using the intent.",
            "mode": "mock" if res is None else "live",
        }
    messages = (res.json() or {}).get("messages") or []
    n = len(messages)
    lines: list[str] = []
    for item in messages[:5]:
        mid = item.get("id")
        if not mid:
            continue
        one = google_get(
            user_id,
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}",
            {"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
        )
        if one is None or one.status_code >= 400:
            continue
        headers = {
            str(h.get("name") or "").lower(): str(h.get("value") or "")
            for h in ((one.json() or {}).get("payload") or {}).get("headers") or []
            if isinstance(h, dict)
        }
        who = headers.get("from") or "unknown"
        subj = headers.get("subject") or "(no subject)"
        lines.append(f"{who} — {subj}")
    evidence = f"Read {n} email" if n == 1 else f"Read {n} emails"
    context = "\n".join(lines) if lines else "No thread titles returned."
    return {
        "ok": True,
        "evidence": evidence,
        "mode": "live",
        "_context": context,
    }


def drive_read_live(intent: str, user_id: str) -> dict[str, Any]:
    q = _search_query(intent).replace("'", "\\'")
    drive_q = f"name contains '{q}' or fullText contains '{q}'"
    res = google_get(
        user_id,
        "https://www.googleapis.com/drive/v3/files",
        {
            "q": drive_q,
            "pageSize": "5",
            "fields": "files(id,name)",
            "spaces": "drive",
        },
    )
    if res is None:
        return {"ok": True, "evidence": "Drive is not connected.", "mode": "mock"}
    if res.status_code >= 400:
        return {"ok": False, "evidence": "Drive read failed.", "mode": "live"}
    files = (res.json() or {}).get("files") or []
    n = len(files)
    names = ", ".join(str(f.get("name") or "") for f in files[:3] if f.get("name"))
    evidence = f"{n} document reviewed" if n == 1 else f"{n} documents reviewed"
    return {
        "ok": True,
        "evidence": evidence,
        "mode": "live",
        "_context": names[:200],
    }


def has_grant(user_id: str | None) -> bool:
    return TOKENS.connected(user_id)


def gmail_send_do(user_id: str, approval_id: str | None, mission: dict) -> dict[str, Any]:
    if not approval_id:
        return {"ok": False, "evidence": "Needs approval.", "gated": True, "mode": "mock"}
    if not has_grant(user_id):
        return {
            "ok": False,
            "evidence": "Gmail is not connected.",
            "gated": True,
            "mode": "mock",
        }
    kind, body = _mail_artifact(mission)
    if not body or body.strip() == (mission.get("intent") or "").strip():
        return {
            "ok": False,
            "evidence": "Nothing to send. Draft is empty or is the prompt.",
            "gated": True,
            "mode": "live",
        }
    if "no emails to summarize" in body.lower():
        return {
            "ok": False,
            "evidence": "Refusing to send an empty summary.",
            "gated": True,
            "mode": "live",
        }
    to_list = _emails(body)
    if not to_list:
        to_list = _emails(mission.get("intent") or "")
    if not to_list:
        me = _gmail_address(user_id)
        if me:
            to_list = [me]
    if not to_list:
        return {"ok": False, "evidence": "Gmail send failed.", "gated": True, "mode": "live"}
    subject = _subject(body, kind)
    raw = _raw_message(to_list, subject, body)
    res = google_post(
        user_id,
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        {"raw": raw},
    )
    if res is None:
        return {
            "ok": False,
            "evidence": "Gmail is not connected.",
            "gated": True,
            "mode": "mock",
        }
    if res.status_code >= 400:
        return {"ok": False, "evidence": "Gmail send failed.", "gated": True, "mode": "live"}
    n = len(to_list)
    return {
        "ok": True,
        "evidence": f"Sent to {n} recipient" if n == 1 else f"Sent to {n} recipients",
        "gated": True,
        "mode": "live",
    }


def calendar_write_do(user_id: str, approval_id: str | None, mission: dict) -> dict[str, Any]:
    if not approval_id:
        return {"ok": False, "evidence": "Needs approval.", "gated": True, "mode": "mock"}
    if not has_grant(user_id):
        return {
            "ok": False,
            "evidence": "Calendar is not connected.",
            "gated": True,
            "mode": "mock",
        }
    summary = "Prep block"
    for art in mission.get("artifacts") or []:
        if art.get("kind") == "calendar" and art.get("body"):
            summary = str(art["body"]).splitlines()[0][:80]
            break
    start = datetime.now(timezone.utc) + timedelta(days=1)
    start = start.replace(hour=13, minute=15, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    res = google_post(
        user_id,
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        {
            "summary": summary,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
        },
    )
    if res is None:
        return {
            "ok": False,
            "evidence": "Calendar is not connected.",
            "gated": True,
            "mode": "mock",
        }
    if res.status_code >= 400:
        return {"ok": False, "evidence": "Calendar write failed.", "gated": True, "mode": "live"}
    return {"ok": True, "evidence": "Prep block written.", "gated": True, "mode": "live"}


def _mail_artifact(mission: dict) -> tuple[str, str]:
    arts = {a.get("kind"): a.get("body") or "" for a in mission.get("artifacts") or []}
    for kind in ("email", "followUp", "agenda", "list", "doc", "brief"):
        body = str(arts.get(kind) or "").strip()
        if body:
            return kind, body
    return "", ""


def _emails(body: str) -> list[str]:
    found = re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", body or "")
    out: list[str] = []
    for addr in found:
        if addr not in out:
            out.append(addr)
    return out[:8]


def _gmail_address(user_id: str) -> str | None:
    res = google_get(user_id, "https://gmail.googleapis.com/gmail/v1/users/me/profile")
    if res is None or res.status_code >= 400:
        return None
    return str((res.json() or {}).get("emailAddress") or "") or None


def _subject(body: str, kind: str) -> str:
    for line in (body or "").splitlines():
        if line.lower().startswith("subject:"):
            return line.split(":", 1)[1].strip()[:120] or "Desk"
        if line.strip():
            return line.strip()[:120]
    return "Desk"


def _raw_message(to_list: list[str], subject: str, body: str) -> str:
    msg = EmailMessage()
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.set_content(body or "")
    return base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")


def _gmail_query(intent: str) -> str:
    t = (intent or "").lower()
    if any(
        w in t
        for w in (
            "inbox",
            "waiting on me",
            "unread",
            "this week",
            "this morning",
            "today",
            "emails i got",
            "summarize",
        )
    ):
        if any(w in t for w in ("this morning", "today")):
            return "in:inbox newer_than:1d"
        return "in:inbox newer_than:7d"
    return _search_query(intent) or "in:inbox"


def _search_query(intent: str) -> str:
    stop = {
        "i",
        "have",
        "a",
        "the",
        "to",
        "and",
        "with",
        "at",
        "for",
        "my",
        "me",
        "it",
        "handle",
        "meeting",
        "tomorrow",
        "today",
        "pm",
        "am",
        "please",
    }
    words = re.findall(r"[A-Za-z0-9]+", intent or "")
    keep = [w for w in words if w.lower() not in stop]
    q = " ".join(keep[:6]).strip()
    return q or "meeting"


def _event_when(start: dict) -> str:
    raw = start.get("dateTime") or start.get("date") or ""
    if not raw:
        return "upcoming"
    try:
        if "T" in raw:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.strftime("%d %b %H:%M")
        return raw
    except ValueError:
        return raw[:16]


def _one_line(text: str, limit: int = 80) -> str:
    line = " ".join(text.split())
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip() + "…"