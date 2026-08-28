import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import type { BoardOutlet } from "../components/AppShell";
import { isDemoBoardId } from "../lib/missions-api";

export default function Approvals() {
  const { pending, doIt, keepDraft, artifactsById } = useOutletContext<BoardOutlet>();
  const [selectedId, setSelectedId] = useState(pending[0]?.id ?? null);
  const [editing, setEditing] = useState(false);

  const rows = pending.filter((p) => !isDemoBoardId(p.mission_id));
  const selected = rows.find((p) => p.id === selectedId) ?? rows[0] ?? null;

  if (rows.length === 0) {
    return <p className="od-approvals-zero">Nothing needs your signature.</p>;
  }

  return (
    <div className="od-approvals">
      <div className="od-approvals-list">
        {rows.map((row) => (
          <div
            key={row.id}
            className={`od-approval-row${row.id === selected?.id ? " is-selected" : ""}`}
            role="button"
            tabIndex={0}
            onClick={() => {
              setSelectedId(row.id);
              setEditing(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setSelectedId(row.id);
                setEditing(false);
              }
            }}
          >
            <p className="od-approval-verb">{row.verb_object}</p>
            <p className="od-approval-parent">{row.parent_intent}</p>
            <p className="od-approval-meta">
              {row.age} · {row.risk}
            </p>
            <div className="od-approval-row-actions">
              <button
                type="button"
                className="od-btn od-btn-do"
                onClick={(e) => {
                  e.stopPropagation();
                  doIt(row.id);
                }}
              >
                Do it
              </button>
              <button
                type="button"
                className="od-btn od-btn-ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  keepDraft(row.id);
                }}
              >
                Keep as draft
              </button>
              <button
                type="button"
                className="od-btn od-btn-ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedId(row.id);
                  setEditing(true);
                }}
              >
                Edit first
              </button>
            </div>
          </div>
        ))}
      </div>
      <aside className="od-approvals-preview">
        {selected ? (
          <>
            <p className="od-preview-kicker">{editing ? "Draft" : "Preview"}</p>
            <h2 className="od-preview-title">{selected.verb_object}</h2>
            <pre className="od-preview-doc">
              {artifactsById[selected.mission_id]?.agenda ?? ""}
            </pre>
          </>
        ) : null}
      </aside>
    </div>
  );
}
