import type { Receipt } from "../lib/types";
import "./ActionReceipt.css";

type Props = {
  receipt: Receipt;
  onApprove?: (actionId: string) => void;
  onDecline?: (actionId: string) => void;
  busy?: boolean;
};

function receiptNumber(id: string): string {
  const raw = id.replace(/^#/, "");
  return `#${raw}`;
}

function elapsedLabel(seconds: number, running: boolean): string {
  if (running && seconds === 0) return "—";
  if (seconds === 1) return "1 second";
  return `${seconds} seconds`;
}

function notSpentLabel(minutes: number): string {
  if (minutes <= 0) return "—";
  if (minutes === 1) return "~1 minute";
  return `~${minutes} minutes`;
}

function stepLine(label: string, detail?: string): string {
  if (!detail) return label;
  return `${label}  (${detail})`;
}

export default function ActionReceipt({
  receipt,
  onApprove,
  onDecline,
  busy,
}: Props) {
  const running = receipt.status === "running";
  const failed = receipt.status === "partial_failure";

  const doneLines = [
    ...receipt.steps.map((s) => ({
      key: `s-${s.label}-${s.detail ?? ""}`,
      mark: s.status === "failed" ? "✕" : "✓",
      failed: s.status === "failed",
      text: stepLine(s.label, s.detail),
    })),
    ...receipt.resolved_actions.map((a) => ({
      key: `r-${a.label}`,
      mark: a.outcome === "approved" ? "✓" : "✕",
      failed: a.outcome === "declined",
      text:
        a.outcome === "declined"
          ? a.label.toLowerCase().includes("draft")
            ? a.label
            : `${a.label.replace(/ — declined$/, "")} · kept as draft`
          : a.label,
    })),
  ];

  const statusNote = running
    ? "Running"
    : receipt.status === "awaiting_approval"
      ? "Waiting on you"
      : failed
        ? "Partial"
        : "Complete";

  return (
    <article
      className="od-receipt"
      data-status={receipt.status}
      aria-live={running ? "polite" : "off"}
    >
      <header className="od-receipt-head">
        <span className="od-receipt-mark">ORION DESK</span>
        <span className="od-receipt-id">
          RECEIPT&nbsp;&nbsp;{receiptNumber(receipt.id)}
          <span className="od-receipt-state">{statusNote}</span>
        </span>
      </header>

      <hr className="od-receipt-rule" />

      <section>
        <div className="od-receipt-kicker">Intent</div>
        <p className="od-receipt-intent">{receipt.intent}</p>
      </section>

      {doneLines.length > 0 ? (
        <>
          <hr className="od-receipt-rule" />
          <section>
            <div className="od-receipt-kicker">Done</div>
            <ul className="od-receipt-lines">
              {doneLines.map((line) => (
                <li
                  key={line.key}
                  className={line.failed ? "is-failed" : undefined}
                >
                  <span className="od-mark" aria-hidden="true">
                    {line.mark}
                  </span>
                  <span>{line.text}</span>
                </li>
              ))}
            </ul>
          </section>
        </>
      ) : null}

      {receipt.pending_actions.length > 0 ? (
        <>
          <hr className="od-receipt-rule" />
          <section className="od-receipt-needs">
            <div className="od-receipt-kicker">Needs you</div>
            {receipt.pending_actions.map((action) => (
              <div key={action.id} className="od-receipt-need-row">
                <p>→ {action.label}</p>
                <div className="od-receipt-actions">
                  <button
                    className="od-btn od-btn-ghost"
                    type="button"
                    disabled={busy}
                    onClick={() => onDecline?.(action.id)}
                  >
                    Keep as draft
                  </button>
                  <button
                    className="od-btn od-btn-do"
                    type="button"
                    disabled={busy}
                    onClick={() => onApprove?.(action.id)}
                  >
                    Do it
                  </button>
                </div>
              </div>
            ))}
          </section>
        </>
      ) : null}

      <hr className="od-receipt-rule" />

      <section>
        <div className="od-receipt-kicker">Tools</div>
        <p className="od-receipt-tools">
          {receipt.tools_used.length ? receipt.tools_used.join(" · ") : "—"}
        </p>
      </section>

      <hr className="od-receipt-rule" />

      <section>
        <div className="od-receipt-kicker">Totals</div>
        <dl className="od-receipt-totals">
          <div>
            <dt>Elapsed</dt>
            <dd>{elapsedLabel(receipt.execution_time_seconds, running)}</dd>
          </div>
          <div>
            <dt>Not spent</dt>
            <dd>{notSpentLabel(receipt.estimated_minutes_saved)}</dd>
          </div>
          <div>
            <dt>Unauthorized actions</dt>
            <dd>{receipt.unauthorized_actions ?? 0}</dd>
          </div>
        </dl>
      </section>

      <p className="od-receipt-legal">
        {receipt.legal ?? "Desk does not send external messages without approval."}
      </p>
    </article>
  );
}
