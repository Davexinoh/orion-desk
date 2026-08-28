import type { Receipt } from "./types";

function padId(id: string): string {
  const raw = id.replace(/^#/, "");
  return `#${raw}`;
}

function stepLine(label: string, detail: string | undefined, failed: boolean): string {
  const mark = failed ? "✕" : "✓";
  const extra = detail ? `  (${detail})` : "";
  return `${mark} ${label}${extra}`;
}

/** Canonical receipt text — identical on web copy and Telegram. */
export function formatReceiptText(r: Receipt): string {
  const id = padId(r.id);
  const lines: string[] = [];
  lines.push(`ORION DESK                    ${id}`);
  lines.push("");
  lines.push("INTENT");
  lines.push(`"${r.intent}"`);
  lines.push("");

  const completed = [
    ...r.steps.map((s) => stepLine(s.label, s.detail, s.status === "failed")),
    ...r.resolved_actions.map((a) =>
      a.outcome === "approved"
        ? `✓ ${a.label}`
        : `✕ ${a.label}`
    ),
  ];

  if (completed.length) {
    lines.push("COMPLETED");
    for (const line of completed) lines.push(line);
    lines.push("");
  }

  if (r.pending_actions.length) {
    lines.push("PENDING APPROVAL");
    for (const a of r.pending_actions) {
      lines.push(`→ ${a.label}`);
    }
    lines.push("");
  }

  const tools = r.tools_used.length ? r.tools_used.join(" · ") : "—";
  const time =
    r.status === "running" && r.execution_time_seconds === 0
      ? "—"
      : `${r.execution_time_seconds}s`;
  const saved =
    r.estimated_minutes_saved > 0 ? `~${r.estimated_minutes_saved} min` : "—";

  lines.push(`Tools used            ${tools}`);
  lines.push(`Execution time         ${time}`);
  lines.push(`Manual effort saved    ${saved}`);
  return lines.join("\n");
}

export function formatReceiptId(n: number): string {
  return `#${String(n).padStart(5, "0")}`;
}

export function formatClock(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const mon = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${mon}-${day} ${hh}:${mm}`;
}

export function statusLabel(status: Receipt["status"]): string {
  switch (status) {
    case "running":
      return "running";
    case "completed":
      return "completed";
    case "awaiting_approval":
      return "awaiting approval";
    case "resolved":
      return "resolved";
    case "partial_failure":
      return "partial failure";
  }
}
