import { Link } from "react-router-dom";
import StudioNav from "../components/StudioNav";
import StudioStage from "../components/StudioStage";
import ActionReceipt from "../components/ActionReceipt";
import {
  ACME_EXAMPLE,
  ACME_ID,
  demoStats,
  receipts,
} from "../lib/demo-data";
import "../styles/landing.css";

const HIDDEN_STEPS = [
  "Find the calendar event",
  "Identify the attendees",
  "Search previous emails",
  "Pull the relevant documents",
  "Review the last meeting notes",
  "Research the company",
  "List unresolved issues",
  "Write an agenda",
  "Draft talking points",
  "Block preparation time",
  "Prepare the follow-up",
  "Remember to actually do it",
];

const LOOP = ["Intent", "Context", "Plan", "Action", "Verification"] as const;

export default function Landing() {
  const receipt = receipts[ACME_ID];

  return (
    <div className="mkt">
      <StudioNav />
      <section className="studio" id="product">
        <StudioStage />
        <div className="studio-copy">
          <p className="studio-kicker">Orion Desk</p>
          <h1>Your intent becomes action.</h1>
          <p className="mkt-sub">
            Tell Desk the outcome. It plans, acts, and stops before anything leaves your name.
          </p>
          <div className="mkt-ctas">
            <a className="mkt-btn mkt-btn-primary" href="https://t.me/oriondesk">
              Open Telegram
            </a>
            <Link className="mkt-btn mkt-btn-ghost" to="/desk/m/acme-0491">
              Watch the Acme demo
            </Link>
          </div>
        </div>
      </section>

      <main>
        <section className="mkt-section">
          <h2>Getting work done is coordination, not tasks.</h2>
          <p className="mkt-acme">{ACME_EXAMPLE}</p>
          <ul className="mkt-hidden">
            {HIDDEN_STEPS.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </section>

        <section className="mkt-section" id="loop">
          <p className="mkt-loop">
            {LOOP.map((w, i) => (
              <span key={w}>
                {i > 0 ? " → " : null}
                {w}
              </span>
            ))}
          </p>
        </section>

        <section className="mkt-section" id="receipt">
          <p className="mkt-caption">Autonomy without a black box.</p>
          <ActionReceipt receipt={receipt} />
        </section>

        <section className="mkt-section" id="demo">
          <Link className="mkt-btn mkt-btn-primary" to="/desk/m/acme-0491">
            Watch the Acme demo
          </Link>
          <p className="mkt-stats">
            {demoStats.actions} actions · {demoStats.integrations} integrations · {demoStats.elapsed} ·{" "}
            {demoStats.notSpent} not spent · {demoStats.unauthorized} unauthorized actions
          </p>
        </section>

        <section className="mkt-section mkt-surfaces">
          <article>
            <h2>Telegram</h2>
            <p>for talking.</p>
          </article>
          <article>
            <h2>Web</h2>
            <p>for seeing.</p>
          </article>
        </section>

        <section className="mkt-section">
          <p className="mkt-safety">Automate the work. Confirm the consequences.</p>
        </section>
      </main>

      <footer className="mkt-footer">
        <p>
          <a href="https://github.com/Davexinoh/orion-desk">GitHub</a>
          {" · "}
          <a href="https://x.com/oriondesk">X</a>
          {" · "}
          <a href="https://t.me/oriondesk">Telegram</a>
          {" · "}
          <a href="https://orionagents.org">orionagents.org</a>
        </p>
        <p>Built for the Orion Agents Builder Hackathon.</p>
      </footer>
    </div>
  );
}
