from __future__ import annotations

import os


def _mode(live: bool) -> str:
    return "live" if live else "mock"


def payload(user_id: str | None = None) -> dict:
    from .google_oauth import TOKENS

    tavily = bool((os.getenv("TAVILY_API_KEY") or "").strip())
    llm = bool(
        (os.getenv("OPENAI_API_KEY") or "").strip()
        or (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    )
    google_on = TOKENS.connected(user_id)
    google = {"connected": google_on, "mode": "mock"}
    return {
        "gmail": dict(google),
        "calendar": dict(google),
        "drive": dict(google),
        "tavily": {"keyPresent": tavily, "mode": _mode(tavily)},
        "llm": {"keyPresent": llm, "mode": _mode(llm)},
    }
