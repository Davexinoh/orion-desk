import ActionReceipt from "../components/ActionReceipt";
import {
  ACME_EXAMPLE,
  ACME_ID,
  artifacts,
  receipts,
} from "../lib/demo-data";

const TICKS = [
  "Found the 2pm event.",
  "Read 6 emails.",
  "Drafted agenda. Not sent.",
];

const AGENDA_PREVIEW = artifacts[ACME_ID].agenda.split("\n").slice(0, 8).join("\n");

export default function TelegramPreview() {
  const receipt = receipts[ACME_ID];

  return (
    <div className="od-tg">
      <h1 className="od-page-title">Telegram templates</h1>
      <p className="od-tg-note">Compressed product. Not a live bot.</p>

      <div className="od-tg-phone">
        <p className="od-tg-label">/start</p>
        <div className="od-tg-msg">
          <p className="od-tg-brand">Orion Desk</p>
          <p>State an outcome.</p>
          <p>Example: I have a meeting with Acme tomorrow at 2. Handle it.</p>
        </div>

        <p className="od-tg-label">User intent</p>
        <div className="od-tg-msg is-user">{ACME_EXAMPLE}</div>

        <p className="od-tg-label">MissionCard</p>
        <div className="od-tg-msg">
          <p className="od-tg-brand">ORION DESK</p>
          <p>Mission · Running</p>
          <p>Prepare me for the Acme meeting.</p>
          <p>6/8 steps</p>
          <p>Calendar · Gmail · Drive · Web</p>
        </div>

        <p className="od-tg-label">TickLines</p>
        <div className="od-tg-msg">
          {TICKS.map((t) => (
            <p key={t}>{t}</p>
          ))}
        </div>

        <p className="od-tg-label">ReceiptBlock</p>
        <div className="od-tg-receipt">
          <ActionReceipt receipt={receipt} />
        </div>

        <p className="od-tg-label">ApprovalKeyboard</p>
        <div className="od-tg-keys" aria-hidden="true">
          <span>Do it</span>
          <span>Keep as draft</span>
          <span>Open receipt</span>
        </div>

        <p className="od-tg-label">ArtifactPreview</p>
        <div className="od-tg-msg od-tg-artifact">
          <pre>{AGENDA_PREVIEW}</pre>
        </div>
      </div>
    </div>
  );
}
