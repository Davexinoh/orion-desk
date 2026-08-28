import { useNavigate, useOutletContext } from "react-router-dom";
import type { BoardOutlet } from "../components/AppShell";
import { ACME_ID, receiptForMission, receipts as seedReceipts } from "../lib/demo-data";
import { isForbiddenSeedCard } from "../lib/missions-api";
import type { Receipt, ReceiptStatus } from "../lib/types";

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

function rowText(r: Receipt, demo = false): string {
  return `${r.id} · ${r.intent} · ${statusText(r.status)} · ${r.execution_time_seconds}s · ${notSpent(r.estimated_minutes_saved)} · ${dateLabel(r.created_at)}${demo ? " · Demo" : ""}`;
}

export default function Receipts() {
  const navigate = useNavigate();
  const { missions, receiptsById, openReceipt } = useOutletContext<BoardOutlet>();
  const rows = missions
    .filter((m) => !isForbiddenSeedCard(m))
    .map((m) => ({
      missionId: m.id,
      receipt: receiptsById[m.id] ?? receiptForMission(m),
    }));

  return (
    <div>
      <h1 className="od-page-title">Receipts</h1>
      <ul className="od-receipt-index">
        {rows.map(({ missionId, receipt: r }) => (
          <li key={r.id}>
            <button type="button" className="od-receipt-index-row" onClick={() => openReceipt(missionId)}>
              {rowText(r)}
            </button>
          </li>
        ))}
        <li>
          <button
            type="button"
            className="od-receipt-index-row"
            onClick={() => navigate(`/desk/m/${ACME_ID}`)}
          >
            {rowText(seedReceipts[ACME_ID], true)}
          </button>
        </li>
        <li>
          <button
            type="button"
            className="od-receipt-index-row"
            onClick={() => navigate("/desk/m/failed-0502")}
          >
            {rowText(seedReceipts["failed-0502"], true)}
          </button>
        </li>
      </ul>
    </div>
  );
}
