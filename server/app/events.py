from __future__ import annotations

import json
from typing import Any, AsyncIterator

ALLOWED = frozenset(
    {
        "mission.started",
        "step.running",
        "step.done",
        "step.blocked",
        "step.failed",
        "artifact.upserted",
        "receipt.updated",
        "approval.needed",
        "mission.waiting_on_you",
        "mission.done",
        "mission.failed",
    }
)
TERMINAL = frozenset({"mission.waiting_on_you", "mission.done", "mission.failed"})

LOG: dict[str, list[dict[str, Any]]] = {}


def emit(mission_id: str, event: dict[str, Any]) -> None:
    typ = event.get("type")
    if typ not in ALLOWED:
        return
    LOG.setdefault(mission_id, []).append(event)


def recorded(mission_id: str) -> list[dict[str, Any]]:
    return list(LOG.get(mission_id) or [])


def replay_from_store(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Rebuild events from persisted rows. Does not call tools."""
    mid = row["id"]
    events: list[dict[str, Any]] = [{"type": "mission.started", "missionId": mid}]
    for step in row.get("steps") or []:
        idx = int(step["index"])
        events.append({"type": "step.running", "stepIndex": idx, "label": step["label"]})
        state = step.get("state") or step.get("status")
        evidence = step.get("evidence") or step.get("detail") or ""
        if state == "done":
            events.append({"type": "step.done", "stepIndex": idx, "evidence": evidence})
        elif state == "failed":
            events.append({"type": "step.failed", "stepIndex": idx, "evidence": evidence})
        elif state == "blocked":
            events.append(
                {
                    "type": "step.blocked",
                    "stepIndex": idx,
                    "reason": evidence or "Needs approval.",
                }
            )
            break
        elif state == "pending" or state == "running":
            break
    for art in row.get("artifacts") or []:
        events.append({"type": "artifact.upserted", "kind": art["kind"]})
    for ap in row.get("approvals") or []:
        if ap.get("status") == "needed":
            events.append({"type": "approval.needed", "approvalId": ap["id"]})
    receipt = row.get("receipt")
    if receipt:
        events.append({"type": "receipt.updated", "receiptId": receipt["id"]})
    status = row.get("status")
    if status == "waiting_on_you":
        events.append({"type": "mission.waiting_on_you"})
    elif status == "failed":
        events.append({"type": "mission.failed"})
    elif status == "done":
        events.append({"type": "mission.done"})
    return [e for e in events if e["type"] in ALLOWED]


def events_for(row: dict[str, Any]) -> list[dict[str, Any]]:
    mid = row["id"]
    live = recorded(mid)
    if live:
        return live
    return replay_from_store(row)


def sse_pack(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, separators=(',', ':'))}\n\n"


async def stream(row: dict[str, Any]) -> AsyncIterator[str]:
    for event in events_for(row):
        yield sse_pack(event)
    # Stream ends after the terminal event. It does not stay open.
