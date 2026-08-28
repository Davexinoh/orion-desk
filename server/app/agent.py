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
    return f"#{n:05d}"


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
    n = STORE.next_seq()
    rid = _rid(n)
    receipt = empty_receipt(rid, intent)
    goal = STORE.get_goal(goal_id) or {
        "id": goal_id,
        "intent": intent,
        "status": "running",
        "created_at": _now(),
        "live_trace": [],
        "artifacts": [],
    }
    goal["receipt_id"] = rid
    goal["status"] = "running"
    STORE.upsert_goal(goal)
    STORE.upsert_receipt(receipt)
    STORE.persist()
    await STORE.publish(rid, {"type": "receipt", "receipt": receipt, "goal": goal, "trace": "On it."})

    meeting = is_meeting_prep(intent)
    plan = ACME_PLAN if meeting else [
        {"delay": 0.6, "label": "Intent parsed", "detail": None, "tool": "Web Search", "trace": "Figuring out what you actually want..."},
        {"delay": 0.8, "label": "Context gathered", "detail": None, "tool": "Web Search", "trace": "Pulling what I can from connected tools..."},
        {"delay": 0.9, "label": "Plan drafted", "detail": "4 steps", "tool": "Drive", "trace": "Breaking it into work I can finish..."},
        {"delay": 1.0, "label": f"Work product generated", "detail": None, "tool": "Drive", "trace": "Writing the output..."},
    ]
    tools: list[str] = []
    started = asyncio.get_event_loop().time()
    context_blob: list[str] = []

    for step in plan:
        await STORE.publish(rid, {"type": "trace", "trace": step["trace"], "receipt": receipt, "goal": goal})
        await asyncio.sleep(step["delay"])
        if step["tool"] not in tools:
            tools.append(step["tool"])
        result = _run_tool(step["label"], intent)
        if result:
            context_blob.append(str(result))
        receipt["steps"].append(
            {"label": step["label"], "detail": step["detail"], "status": "done"}
        )
        receipt["tools_used"] = list(tools)
        receipt["execution_time_seconds"] = max(1, int(asyncio.get_event_loop().time() - started))
        receipt["estimated_minutes_saved"] = (12 + len(receipt["steps"]) * 5) if meeting else (8 + len(receipt["steps"]) * 3)
        goal["live_trace"] = (goal.get("live_trace") or []) + [step["trace"]]
        STORE.upsert_receipt(receipt)
        STORE.upsert_goal(goal)
        await STORE.publish(rid, {"type": "receipt", "receipt": receipt, "goal": goal, "trace": step["trace"]})

    if meeting:
        artifacts = [dict(a) for a in ACME_ARTIFACTS]
        llm = await _maybe_llm_brief(intent, artifacts[0]["body"] + "\n\n" + "\n".join(context_blob))
        if llm:
            artifacts[0] = {**artifacts[0], "body": llm}
        receipt.update(
            {
                "status": "awaiting_approval",
                "pending_actions": [dict(ACME_PENDING)],
                "tools_used": ["Calendar", "Gmail", "Drive", "Web Search"],
                "execution_time_seconds": max(receipt["execution_time_seconds"], 1),
                "estimated_minutes_saved": 47,
            }
        )
        goal["status"] = "awaiting_approval"
        goal["artifacts"] = artifacts
        goal["live_trace"] = goal["live_trace"] + ["One thing needs your OK before I send it."]
        STORE.state["time_saved_minutes"] = STORE.state.get("time_saved_minutes", 0) + 47
        STORE.upsert_receipt(receipt)
        STORE.upsert_goal(goal)
        STORE.persist()
        await STORE.publish(
            rid,
            {
                "type": "receipt",
                "receipt": receipt,
                "goal": goal,
                "trace": "One thing needs your OK before I send it.",
            },
        )
        return receipt

    receipt["status"] = "completed"
    goal["status"] = "completed"
    STORE.state["time_saved_minutes"] = STORE.state.get("time_saved_minutes", 0) + receipt["estimated_minutes_saved"]
    STORE.upsert_receipt(receipt)
    STORE.upsert_goal(goal)
    STORE.persist()
    await STORE.publish(
        rid,
        {"type": "receipt", "receipt": receipt, "goal": goal, "trace": "Done. Here's everything I did."},
    )
    return receipt


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
    receipt = STORE.get_receipt(receipt_id)
    if not receipt:
        return None
    next_r = resolve_action(receipt, action_id, outcome)
    if outcome == "approved" and action_id == "send-agenda":
        from . import tools as tool_layer

        tool_layer.send_email({"to": "attendees", "subject": "Agenda — Acme Q3 expansion review"})
    STORE.upsert_receipt(next_r)
    goal = STORE.get_goal(next_r["id"])
    if goal:
        goal["status"] = next_r["status"]
        STORE.upsert_goal(goal)
    STORE.add_memory(
        {
            "id": f"ex-{int(datetime.now().timestamp() * 1000)}",
            "layer": "execution",
            "title": f"Receipt {next_r['id']}",
            "body": (next_r["resolved_actions"] or [{}])[-1].get("label", ""),
            "receipt_id": next_r["id"],
            "updated_at": _now(),
        }
    )
    STORE.persist()
    await STORE.publish(next_r["id"], {"type": "receipt", "receipt": next_r, "goal": goal, "trace": None})
    q = TELEGRAM_WAITERS.get(next_r["id"])
    if q:
        await q.put(next_r)
    return next_r
