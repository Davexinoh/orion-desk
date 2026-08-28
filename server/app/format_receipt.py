"""Canonical receipt text — keep in lockstep with web/src/lib/format.ts."""

from __future__ import annotations


def format_receipt(r: dict) -> str:
    rid = r["id"] if str(r["id"]).startswith("#") else f"#{r['id']}"
    lines: list[str] = []
    lines.append(f"ORION DESK                    {rid}")
    lines.append("")
    lines.append("INTENT")
    lines.append(f"\"{r['intent']}\"")
    lines.append("")

    completed: list[str] = []
    for s in r.get("steps") or []:
        mark = "✕" if s.get("status") == "failed" else "✓"
        extra = f"  ({s['detail']})" if s.get("detail") else ""
        completed.append(f"{mark} {s['label']}{extra}")
    for a in r.get("resolved_actions") or []:
        if a.get("outcome") == "approved":
            completed.append(f"✓ {a['label']}")
        else:
            completed.append(f"✕ {a['label']}")

    if completed:
        lines.append("COMPLETED")
        lines.extend(completed)
        lines.append("")

    pending = r.get("pending_actions") or []
    if pending:
        lines.append("PENDING APPROVAL")
        for a in pending:
            lines.append(f"→ {a['label']}")
        lines.append("")

    tools = r.get("tools_used") or []
    tools_s = " · ".join(tools) if tools else "—"
    running = r.get("status") == "running"
    seconds = r.get("execution_time_seconds") or 0
    time_s = "—" if running and seconds == 0 else f"{seconds}s"
    saved = r.get("estimated_minutes_saved") or 0
    saved_s = f"~{saved} min" if saved > 0 else "—"

    lines.append(f"Tools used            {tools_s}")
    lines.append(f"Execution time         {time_s}")
    lines.append(f"Manual effort saved    {saved_s}")
    return "\n".join(lines)
