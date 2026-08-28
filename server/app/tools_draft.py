from __future__ import annotations

import os
from typing import Any

import httpx




def llm_configured() -> bool:
    return bool(_openai_key() or _anthropic_key())


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def _anthropic_key() -> str:
    return (os.getenv("ANTHROPIC_API_KEY") or "").strip()


def _provider() -> str:
    pref = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
    if pref == "anthropic" and _anthropic_key():
        return "anthropic"
    if _openai_key():
        return "openai"
    if _anthropic_key():
        return "anthropic"
    return ""


def doc_draft_live(intent: str, label: str, prior_evidence: list[str] | None) -> dict[str, Any]:
    from .tools_mock import _draft_body

    kind, title, fallback = _draft_body(intent, label)
    if kind == "calendar":
        return {
            "ok": True,
            "evidence": "Draft written. Not sent.",
            "artifact": {"kind": kind, "title": title, "body": fallback},
            "mode": "mock",
        }
    body = _complete(kind, intent, prior_evidence or [])
    if body is None:
        return {"ok": False, "evidence": "Draft failed.", "mode": "live"}
    body = _strip_sent_claim(body) or fallback
    return {
        "ok": True,
        "evidence": "Draft written. Not sent.",
        "artifact": {"kind": kind, "title": title, "body": body},
        "mode": "live",
    }


def _complete(kind: str, intent: str, prior: list[str]) -> str | None:
    evidence = "\n".join(prior[:12]) if prior else "(none)"
    system = (
        "You write a short {kind} for Orion Desk. "
        "Use only the intent and evidence. "
        "Do not invent facts. Never say the message was sent, emailed, or delivered. "
        "Plain text only."
    ).format(kind=kind)
    user = f"Intent:\n{intent}\n\nEvidence:\n{evidence}\n\nWrite the {kind}."
    provider = _provider()
    if provider == "openai":
        return _openai(system, user)
    if provider == "anthropic":
        return _anthropic(system, user)
    return None


def _openai(system: str, user: str) -> str | None:
    key = _openai_key()
    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    try:
        with httpx.Client(timeout=20) as client:
            res = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 700,
                    "temperature": 0.2,
                },
            )
            res.raise_for_status()
            data = res.json()
        text = data["choices"][0]["message"]["content"]
        return str(text).strip() or None
    except Exception:
        return None


def _anthropic(system: str, user: str) -> str | None:
    key = _anthropic_key()
    model = (os.getenv("ANTHROPIC_MODEL") or "claude-3-5-haiku-20241022").strip()
    try:
        with httpx.Client(timeout=20) as client:
            res = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 700,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            res.raise_for_status()
            data = res.json()
        parts = data.get("content") or []
        text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
        return text.strip() or None
    except Exception:
        return None


def _strip_sent_claim(body: str) -> str:
    lines = []
    for line in body.splitlines():
        low = line.lower()
        if "was sent" in low or "has been sent" in low or "email sent" in low:
            continue
        lines.append(line)
    text = "\n".join(lines).strip()
    if "not sent" not in text.lower() and text:
        text = text.rstrip() + "\n\nNot sent."
    return text
