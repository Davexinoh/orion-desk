import { useOutletContext } from "react-router-dom";
import type { BoardOutlet } from "../components/AppShell";
import { receipts } from "../lib/demo-data";
import type { ReceiptStatus } from "../lib/types";

function statusText(status: ReceiptStatus): string {
  switch (status) {
    case "awaiting_approval":
      return "Waiting on you";
    case "running":
      return "Running";
    case "completed":
    case "resolved":
      return "Done";
    case "partial_failure":
      return "Failed";
  }
}

function notSpent(minutes: number): string {
  if (minutes <= 0) return "—";
  return `~${minutes} min not spent`;
}

function dateLabel(iso: string): string {
  return iso.slice(0, 10);
}

export default function Receipts() {
  const { openReceipt } = useOutletContext<BoardOutlet>();
  const rows = Object.entries(receipts);

  return (
    <div>
      <h1 className="od-page-title">Receipts</h1>
      <ul className="od-receipt-index">
        {rows.map(([missionId, r]) => (
          <li key={r.id}>
            <button type="button" className="od-receipt-index-row" onClick={() => openReceipt(missionId)}>
              {r.id} · {r.intent} · {statusText(r.status)} · {r.execution_time_seconds}s ·{" "}
              {notSpent(r.estimated_minutes_saved)} · {dateLabel(r.created_at)}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
