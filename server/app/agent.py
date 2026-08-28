from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

import httpx

from .demo_data import ACME_ARTIFACTS, ACME_PENDING, ACME_PLAN, is_meeting_prep
from .store import STORE
from . import tools as tool_layer

TELEGRAM_WAITERS: dict[str, asyncio.Queue] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rid(n: int) -> str:
    raise RuntimeError("dead path")


def empty_receipt(rid: str, intent: str) -> dict:
    return {
        "id": rid,
        "intent": intent,
        "status": "running",
        "steps": [],
        "pending_actions": [],
        "resolved_actions": [],
        "tools_used": [],
        "execution_time_seconds": 0,
        "estimated_minutes_saved": 0,
        "created_at": _now(),
    }


async def _maybe_llm_brief(intent: str, context: str) -> str | None:
    xai = os.getenv("XAI_API_KEY")
    oai = os.getenv("OPENAI_API_KEY")
    if not xai and not oai:
        return None
    if xai:
        url = "https://api.x.ai/v1/chat/completions"
        model = os.getenv("XAI_MODEL", "grok-3-mini")
        key = xai
    else:
        url = "https://api.openai.com/v1/chat/completions"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        key = oai
    prompt = (
        "You are Orion Desk. Write a concise meeting briefing from the context. "
        "Literal, specific, no fluff. Use short sections.\n\n"
        f"Intent: {intent}\n\nContext:\n{context}"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                url,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "Write the briefing only."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


async def run_goal(goal_id: str, intent: str) -> dict:
    raise RuntimeError("dead: use POST /missions")


def _run_tool(label: str, intent: str) -> dict | None:
    if label == "Calendar inspected":
        return tool_layer.calendar_inspect(intent)
    if label == "Email history analyzed":
        return tool_layer.gmail_search(intent)
    if label == "Documents retrieved":
        return tool_layer.drive_search(intent)
    if label == "External research completed":
        return tool_layer.web_research("Acme")
    return None


def resolve_action(receipt: dict, action_id: str, outcome: str) -> dict:
    action = next((a for a in receipt["pending_actions"] if a["id"] == action_id), None)
    if not action:
        return receipt
    remaining = [a for a in receipt["pending_actions"] if a["id"] != action_id]
    if action_id == "send-agenda":
        label = (
            "Agenda sent to 4 attendees"
            if outcome == "approved"
            else "Agenda not sent — declined"
        )
    elif outcome == "approved":
        label = action["label"].replace("Send ", "Sent ", 1)
    else:
        label = f"{action['label']} — declined"
    receipt = {
        **receipt,
        "pending_actions": remaining,
        "resolved_actions": receipt.get("resolved_actions", [])
        + [{"label": label, "outcome": outcome}],
        "status": "awaiting_approval" if remaining else "resolved",
    }
    return receipt


async def apply_resolution(receipt_id: str, action_id: str, outcome: str) -> dict | None:
    raise RuntimeError("dead: use POST /approvals")
