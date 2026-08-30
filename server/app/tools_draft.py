from __future__ import annotations

import os
from typing import Any


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
            "evidence": "Prep block proposed. Not written.",
            "artifact": {"kind": kind, "title": title, "body": fallback},
            "mode": "mock",
        }
    body = _complete(kind, intent, prior_evidence or [])
    if body is None:
        print(f"draft fallback kind={kind} provider={_provider() or 'none'}")
        return {
            "ok": True,
            "evidence": "Draft used the template. Model did not return text.",
            "artifact": {"kind": kind, "title": title, "body": fallback},
            "mode": "live",
        }
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
        "You are Orion Desk, a personal assistant. "
        f"Write a complete, usable {kind} that fulfills the user's intent. "
        "The evidence is context, not the deliverable. "
        "If they asked for a recipe: dish name, servings, timing, ingredients, steps. "
        "If they asked for a list: the list. "
        "If they asked for a brief or agenda: that document. "
        "Do not title it Orion Desk Documentation. "
        "Do not paste the evidence log back. "
        "Never say the work was sent or emailed. "
        "Plain text."
    )
    user = (
        f"Intent:\n{intent}\n\n"
        f"Context from tools:\n{evidence}\n\n"
        f"Write the {kind} now."
    )
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
        import httpx

        with httpx.Client(timeout=30) as client:
            res = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 900,
                    "temperature": 0.4,
                },
            )
            if res.status_code >= 400:
                print(f"openai draft failed status={res.status_code}")
                return None
            data = res.json()
        text = data["choices"][0]["message"]["content"]
        return str(text).strip() or None
    except Exception as exc:
        print(f"openai draft failed model={model} err={type(exc).__name__}")
        return None


def _anthropic(system: str, user: str) -> str | None:
    key = _anthropic_key()
    model = (os.getenv("ANTHROPIC_MODEL") or "claude-3-5-haiku-20241022").strip()
    try:
        import httpx

        with httpx.Client(timeout=30) as client:
            res = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 900,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            if res.status_code >= 400:
                print(f"anthropic draft failed status={res.status_code}")
                return None
            data = res.json()
        parts = data.get("content") or []
        text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
        return text.strip() or None
    except Exception as exc:
        print(f"anthropic draft failed model={model} err={type(exc).__name__}")
        return None


def _strip_sent_claim(body: str) -> str:
    lines = []
    for line in body.splitlines():
        low = line.lower()
        if "was sent" in low or "has been sent" in low or "email sent" in low:
            continue
        lines.append(line)
    return "\n".join(lines).strip()
