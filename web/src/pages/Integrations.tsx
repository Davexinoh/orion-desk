import { useDesk } from "../lib/store";

const GOOGLE = new Set(["gmail", "calendar", "drive"]);

export default function Integrations() {
  const { state } = useDesk();

  return (
    <div>
      <div className="page-head">
        <h1>Integrations</h1>
        <p>
          Phase 1 tools. Demo data is loaded so you can run the meeting-prep
          flow without OAuth. Connect Google when you want it on your account.
        </p>
      </div>

      <div className="integ-table">
        {state.integrations.map((item) => (
          <div key={item.id} className="integ-row">
            <div>
              <div style={{ fontWeight: 500 }}>{item.name}</div>
              <div className="sub">{item.required_for}</div>
            </div>
            <div className="sub">{item.role}</div>
            <div>
              <span className={item.connected ? "badge ok" : "badge"}>
                {item.connected ? "ready" : "demo"}
              </span>
              {GOOGLE.has(item.id) ? (
                <div className="sub" style={{ marginTop: 8 }}>
                  Connect Google in server env to go live.
                </div>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      <p className="section-lead" style={{ marginTop: 32 }}>
        {state.integrations.find((i) => i.id === "gmail")?.status} Telegram
        needs a bot token in the server env. Notion, Slack, and voice are
        Phase 2 — not required for this desk.
      </p>
    </div>
  );
}
