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
    if res is None:
        return {"ok": True, "evidence": "Calendar is not connected.", "mode": "mock"}
    if res.status_code >= 400:
        return {"ok": False, "evidence": "Calendar read failed.", "mode": "live"}
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
    q = _search_query(intent)
    res = google_get(
        user_id,
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        {"q": q, "maxResults": "10"},
    )
    if res is None:
        return {"ok": True, "evidence": "Gmail is not connected.", "mode": "mock"}
    if res.status_code >= 400:
        return {"ok": False, "evidence": "Gmail search failed.", "mode": "live"}
    messages = (res.json() or {}).get("messages") or []
    n = len(messages)
    context = ""
    if messages:
        mid = messages[0].get("id")
        if mid:
            one = google_get(
                user_id,
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}",
                {"format": "metadata", "metadataHeaders": "Subject"},
            )
            if one is not None and one.status_code < 400:
                snippet = str((one.json() or {}).get("snippet") or "")
                context = snippet[:200]
    evidence = f"Read {n} email" if n == 1 else f"Read {n} emails"
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
    to_list = _emails(body)
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
        "evidence": f"Agenda sent to {n} attendees",
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
    if arts.get("agenda"):
        return "agenda", str(arts["agenda"])
    if arts.get("followUp"):
        return "followUp", str(arts["followUp"])
    return "agenda", mission.get("intent") or ""


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
            return line.split(":", 1)[1].strip()[:120] or "Agenda"
    return "Agenda" if kind == "agenda" else "Follow-up"


def _raw_message(to_list: list[str], subject: str, body: str) -> str:
    msg = EmailMessage()
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.set_content(body or "")
    return base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")


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
