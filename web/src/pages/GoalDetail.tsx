import { Link, useParams } from "react-router-dom";
import ActionReceipt from "../components/ActionReceipt";
import { useDesk } from "../lib/store";

export default function GoalDetail() {
  const { id } = useParams();
  const { goalById, receiptById, liveTrace, approve, decline, state } = useDesk();
  const goal = id ? goalById(id) : undefined;
  const receipt = goal ? receiptById(goal.receipt_id) : id ? receiptById(id) : undefined;

  if (!goal && !receipt) {
    return (
      <div className="empty">
        <strong>That run is not on this desk.</strong>
        It may have been from another session.{" "}
        <Link to="/desk">Back home</Link>.
      </div>
    );
  }

  const r = receipt;
  const trace = goal?.live_trace ?? [];
  const current = r ? liveTrace[r.id] : "";
  const running = r?.status === "running";
  const tools = r?.tools_used.length ?? 0;
  const steps = (r?.steps.length ?? 0) + (r?.resolved_actions.length ?? 0);

  return (
    <div>
      <div className="page-head">
        <h1>{running ? "Working" : r?.status === "awaiting_approval" ? "Needs you" : "Done. Here's everything I did."}</h1>
        <p>{goal?.intent ?? r?.intent}</p>
      </div>

      {running && trace.length > 0 ? (
        <div className="trace" aria-live="polite">
          {trace.slice(-6).map((line, i) => (
            <div key={`${line}-${i}`} className={i === trace.slice(-6).length - 1 ? "now" : ""}>
              {i === trace.slice(-6).length - 1 ? "▸ " : "  "}
              {line}
            </div>
          ))}
        </div>
      ) : current && running ? (
        <div className="trace">
          <div className="now">▸ {current}</div>
        </div>
      ) : null}

      {r ? (
        <ActionReceipt
          receipt={r}
          onApprove={(actionId) => approve(r.id, actionId)}
          onDecline={(actionId) => decline(r.id, actionId)}
        />
      ) : (
        <div className="empty">
          <strong>Opening the run…</strong>
          {current || "On it."}
        </div>
      )}

      {goal && goal.artifacts.length > 0
        ? goal.artifacts.map((a) => (
            <article key={a.title} className="artifact">
              <h3>{a.title}</h3>
              <pre>{a.body}</pre>
            </article>
          ))
        : null}

      {r && r.status !== "running" ? (
        <p className="summary-strip">
          <span>
            <strong>{steps}</strong> actions
          </span>
          <span>
            <strong>{tools}</strong> integrations
          </span>
          <span>
            <strong>{r.execution_time_seconds}s</strong> elapsed
          </span>
          <span>
            <strong>{r.estimated_minutes_saved} min</strong> estimated manual work avoided
          </span>
          <span>
            <strong>0</strong> unauthorized actions
          </span>
        </p>
      ) : null}

      {state.goals.length > 1 ? (
        <p className="section-lead" style={{ marginTop: 32 }}>
          <Link to="/desk/receipts">All receipts →</Link>
        </p>
      ) : null}
    </div>
  );
}
