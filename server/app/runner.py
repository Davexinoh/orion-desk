from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from .events import emit
from .mission_seed import ACME_ID, LEGAL
from .mission_store import MISSIONS
from .planner import looks_like_acme, looks_like_meeting, plan
from .tools_mock import ADAPTERS, AUTO, GATED, TOOL_LABELS


def run_mission(user_id: str, intent: str) -> dict:
    started = time.perf_counter()
    now = datetime.now(timezone.utc)
    mid = _new_id()
    steps = plan(intent)
    tools = _display_tools(steps)
    tool_names = [s["tool"] for s in steps if s.get("tool")]
    MISSIONS.create(
        {
            "id": mid,
            "userId": user_id,
            "intent": intent,
            "status": "running",
            "toolNames": tool_names,
            "tools": tools,
            "startedAt": now.isoformat(),
            "started_label": f"{now.hour}:{now.minute:02d}",
            "elapsedMs": 0,
            "notSpentMinutes": 47 if looks_like_acme(intent) else 20,
            "unauthorized": 0,
            "steps": [
                {
                    "id": f"{mid}-s{i}",
                    "index": i,
                    "label": s["label"],
                    "state": "pending",
                    "evidence": None,
                    "tool": s.get("tool"),
                }
                for i, s in enumerate(steps, start=1)
            ],
        }
    )
    emit(mid, {"type": "mission.started", "missionId": mid})

    if steps and steps[0].get("failed"):
        MISSIONS.set_step(mid, 1, "failed", "Planner rejected the plan.")
        _write_receipt(mid, intent, tools, started, status="partial_failure")
        MISSIONS.set_status(mid, "failed", _elapsed(started))
        emit(mid, {"type": "mission.failed"})
        row = MISSIONS.get(mid)
        assert row
        return row

    blocked = False
    failed = False
    prior: list[str] = []
    try:
        for i, spec in enumerate(steps, start=1):
            label = spec["label"]
            tool = spec.get("tool")
            emit(mid, {"type": "step.running", "stepIndex": i, "label": label})
            if tool in GATED:
                MISSIONS.set_step(mid, i, "blocked", "Needs approval.")
                emit(mid, {"type": "step.blocked", "stepIndex": i, "reason": "Needs approval."})
                ap = _approval(mid, user_id, intent)
                MISSIONS.add_approval(ap)
                emit(mid, {"type": "approval.needed", "approvalId": ap["id"]})
                blocked = True
                break
            result = _run_auto(tool, intent, label, user_id, prior)
            if not result.get("ok"):
                MISSIONS.set_step(mid, i, "failed", result.get("evidence") or "Step failed.")
                emit(
                    mid,
                    {
                        "type": "step.failed",
                        "stepIndex": i,
                        "evidence": result.get("evidence") or "Step failed.",
                    },
                )
                failed = True
                break
            evidence = result.get("evidence")
            MISSIONS.set_step(mid, i, "done", evidence)
            emit(mid, {"type": "step.done", "stepIndex": i, "evidence": evidence or ""})
            if evidence:
                prior.append(f"{label}: {evidence}")
            extra = result.get("_context")
            if extra:
                prior.append(str(extra))
            art = result.get("artifact")
            if art:
                MISSIONS.upsert_artifact(
                    mid,
                    {
                        "kind": art["kind"],
                        "title": art["title"],
                        "body": art["body"],
                        "sent": False,
                    },
                )
                emit(mid, {"type": "artifact.upserted", "kind": art["kind"]})
    except Exception as exc:
        failed = True
        emit(mid, {"type": "step.failed", "stepIndex": 0, "evidence": "Run failed."})
        del exc

    receipt_status = "awaiting_approval" if blocked else "partial_failure" if failed else "completed"
    mission_status = "waiting_on_you" if blocked else "failed" if failed else "done"
    rec = _write_receipt(mid, intent, tools, started, status=receipt_status)
    emit(mid, {"type": "receipt.updated", "receiptId": rec["id"]})
    MISSIONS.set_status(mid, mission_status, _elapsed(started))
    terminal = {
        "waiting_on_you": "mission.waiting_on_you",
        "failed": "mission.failed",
        "done": "mission.done",
    }[mission_status]
    emit(mid, {"type": terminal})
    row = MISSIONS.get(mid)
    assert row
    return row


def _run_auto(
    tool: str | None, intent: str, label: str, user_id: str, prior: list[str]
) -> dict:
    if not tool:
        return {"ok": True, "evidence": "Intent read.", "mode": "mock"}
    if tool not in AUTO:
        return {"ok": False, "evidence": "Unknown tool.", "mode": "mock"}
    fn = ADAPTERS[tool]
    result = fn(intent=intent, label=label, user_id=user_id, prior_evidence=prior)
    result.setdefault("mode", "mock")
    return result


def _approval(mid: str, user_id: str, intent: str) -> dict:
    if looks_like_acme(intent):
        verb = "Send agenda to Jane, Mark, Priya, Dan"
        bar = "Send agenda to 4 attendees"
        kind = "agenda"
        action = "send-agenda"
    elif looks_like_meeting(intent):
        verb = "Send agenda to attendees"
        bar = "Send agenda to attendees"
        kind = "agenda"
        action = "send-agenda"
    else:
        verb = "Send the draft"
        bar = "Send the draft"
        kind = "doc"
        action = "send-draft"
    return {
        "id": f"ap-{mid}",
        "mission_id": mid,
        "userId": user_id,
        "verbObject": verb,
        "risk": "External send",
        "artifactKind": kind,
        "status": "needed",
        "action_id": action,
        "bar_label": bar,
        "parent_intent": intent,
        "age": "now",
    }


def _write_receipt(
    mid: str, intent: str, tools: list[str], started: float, status: str
) -> dict:
    row = MISSIONS.get(mid)
    assert row
    done = []
    for s in row["steps"]:
        if s["state"] == "done":
            item = {"label": s["label"], "status": "done"}
            if s.get("evidence"):
                item["detail"] = s["evidence"]
            done.append(item)
        elif s["state"] == "failed":
            item = {"label": s["label"], "status": "failed"}
            if s.get("evidence"):
                item["detail"] = s["evidence"]
            done.append(item)
    pending = []
    for ap in row.get("approvals") or []:
        if ap.get("status") == "needed":
            pending.append({"id": ap.get("action_id") or ap["id"], "label": ap.get("bar_label")})
    rid = MISSIONS.next_receipt_id()
    receipt = {
        "id": rid,
        "intent": intent,
        "status": status,
        "steps": done,
        "pending_actions": pending,
        "resolved_actions": [],
        "tools_used": tools,
        "execution_time_seconds": _elapsed(started) // 1000,
        "estimated_minutes_saved": row.get("notSpentMinutes") or 0,
        "unauthorized_actions": 0,
        "legal": LEGAL,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    MISSIONS.upsert_receipt(mid, receipt)
    return receipt


def _display_tools(steps: list[dict]) -> list[str]:
    names = []
    for s in steps:
        tool = s.get("tool")
        if not tool:
            continue
        label = TOOL_LABELS.get(tool, tool)
        if label not in names:
            names.append(label)
    return names


def _elapsed(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _new_id() -> str:
    for _ in range(8):
        mid = f"m-{uuid4().hex[:8]}"
        if mid != ACME_ID and not MISSIONS.exists(mid):
            return mid
    raise RuntimeError("Could not allocate mission id.")
