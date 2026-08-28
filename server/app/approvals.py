from __future__ import annotations

from datetime import datetime, timezone

from .events import emit
from .mission_seed import LEGAL, PUBLIC_IDS
from .mission_store import MISSIONS
from .tools_google import calendar_write_do, gmail_send_do
from .users import USERS


class ApprovalError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(detail)


def _owned(ap: dict, user_id: str) -> None:
    if not ap:
        raise ApprovalError(404, "Approval not found.")
    mid = ap.get("mission_id") or ap.get("missionId")
    if mid in PUBLIC_IDS or not ap.get("userId") or ap.get("userId") != user_id:
        raise ApprovalError(403, "Not owner.")


def list_needed(user_id: str) -> list[dict]:
    return MISSIONS.list_needed(user_id)


def do_approval(user_id: str, approval_id: str) -> dict:
    ap = MISSIONS.get_approval(approval_id)
    _owned(ap, user_id)
    if ap["status"] != "needed":
        raise ApprovalError(409, "Not needed.")
    mid = ap["mission_id"]
    mission = MISSIONS.get(mid)
    if not mission:
        raise ApprovalError(404, "Approval not found.")
    blocked = next((s for s in mission["steps"] if s["state"] == "blocked"), None)
    if not blocked:
        raise ApprovalError(409, "Not needed.")
    tool = blocked.get("tool")
    policy = ((USERS.get(user_id) or {}).get("approvalPolicy") or "all_writes")
    risk = ap.get("risk") or ""
    if tool == "gmail.send":
        result = gmail_send_do(user_id, approval_id, mission)
    elif tool == "calendar.write" and (
        risk == "Calendar write" or policy == "all_writes"
    ):
        result = calendar_write_do(user_id, approval_id, mission)
    else:
        raise ApprovalError(409, "Not needed.")
    evidence = result.get("evidence") or "Step failed."
    idx = int(blocked["index"])
    if not result.get("ok"):
        MISSIONS.set_step(mid, idx, "failed", evidence)
        mission = MISSIONS.get(mid)
        assert mission
        receipt = _receipt(mission, awaiting=True, bar="")
        MISSIONS.upsert_receipt(mid, receipt)
        MISSIONS.set_status(mid, "failed", int(mission.get("elapsedMs") or 0))
        emit(mid, {"type": "step.failed", "stepIndex": idx, "evidence": evidence})
        emit(mid, {"type": "receipt.updated", "receiptId": receipt["id"]})
        emit(mid, {"type": "mission.failed"})
        row = MISSIONS.get(mid)
        assert row
        return row
    MISSIONS.set_step(mid, idx, "done", evidence)
    kinds = []
    if ap.get("artifactKind"):
        kinds.append(ap["artifactKind"])
    if tool == "gmail.send":
        kinds.extend(["agenda", "followUp"])
    elif tool == "calendar.write":
        kinds.append("calendar")
    for kind in dict.fromkeys(kinds):
        MISSIONS.mark_artifact_sent(mid, kind)
    MISSIONS.set_approval_status(approval_id, "approved")
    mission = MISSIONS.get(mid)
    assert mission
    still_blocked = any(s["state"] == "blocked" for s in mission["steps"])
    still_needed = any(a.get("status") == "needed" for a in mission.get("approvals") or [])
    done = not still_blocked and not still_needed
    receipt = _receipt(mission, awaiting=not done, bar=ap.get("bar_label") or "")
    MISSIONS.upsert_receipt(mid, receipt)
    status = "waiting_on_you" if not done else "done"
    MISSIONS.set_status(mid, status, int(mission.get("elapsedMs") or 0))
    emit(mid, {"type": "step.done", "stepIndex": idx, "evidence": evidence})
    emit(mid, {"type": "receipt.updated", "receiptId": receipt["id"]})
    if done:
        emit(mid, {"type": "mission.done"})
    row = MISSIONS.get(mid)
    assert row
    return row


def keep_draft(user_id: str, approval_id: str) -> dict:
    ap = MISSIONS.get_approval(approval_id)
    _owned(ap, user_id)
    if ap["status"] != "needed":
        raise ApprovalError(409, "Not needed.")
    mission = MISSIONS.get(ap["mission_id"])
    if not mission:
        raise ApprovalError(404, "Approval not found.")
    return mission


def _receipt(mission: dict, awaiting: bool, bar: str) -> dict:
    prev = mission.get("receipt") or {}
    steps = []
    for s in mission["steps"]:
        if s["state"] in ("done", "failed"):
            item = {"label": s["label"], "status": s["state"]}
            if s.get("evidence"):
                item["detail"] = s["evidence"]
            steps.append(item)
    pending = []
    resolved = list(prev.get("resolved_actions") or [])
    if not awaiting and bar:
        resolved.append({"label": bar, "outcome": "approved"})
    elif awaiting:
        for ap in mission.get("approvals") or []:
            if ap.get("status") == "needed":
                pending.append({"id": ap.get("action_id") or ap["id"], "label": ap.get("bar_label")})
    return {
        "id": prev.get("id") or MISSIONS.next_receipt_id(),
        "intent": mission["intent"],
        "status": "awaiting_approval" if awaiting else "completed",
        "steps": steps,
        "pending_actions": pending,
        "resolved_actions": resolved,
        "tools_used": mission.get("tools") or [],
        "execution_time_seconds": int(mission.get("elapsed_seconds") or 0),
        "estimated_minutes_saved": mission.get("notSpentMinutes") or 0,
        "unauthorized_actions": 0,
        "legal": prev.get("legal") or LEGAL,
        "created_at": prev.get("created_at") or datetime.now(timezone.utc).isoformat(),
    }
