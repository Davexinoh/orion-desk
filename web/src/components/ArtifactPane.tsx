import { useEffect, useState } from "react";
import type { MissionArtifacts } from "../lib/demo-data";

const LABELS: Record<string, string> = {
  recipe: "Recipe",
  list: "List",
  doc: "Document",
  brief: "Brief",
  agenda: "Agenda",
  calendar: "Calendar",
  email: "Email",
  followUp: "Follow-up",
};

const ORDER = [
  "recipe",
  "list",
  "doc",
  "brief",
  "agenda",
  "email",
  "followUp",
  "calendar",
];

type Props = {
  artifacts?: MissionArtifacts;
};

export default function ArtifactPane({ artifacts }: Props) {
  const keys = ORDER.filter((k) => {
    const v = artifacts?.[k as keyof MissionArtifacts];
    return typeof v === "string" && v.trim();
  });
  const tabs = keys.length ? keys : [];
  const [tab, setTab] = useState(tabs[0] || "");

  useEffect(() => {
    if (tabs.length && !tabs.includes(tab)) setTab(tabs[0]);
  }, [tabs.join("|")]);

  if (!tabs.length) {
    return (
      <div className="od-artifacts">
        <div className="od-artifact-paper">
          <p className="od-artifact-empty">No document yet.</p>
        </div>
      </div>
    );
  }

  const body = artifacts?.[tab as keyof MissionArtifacts];

  return (
    <div className="od-artifacts">
      <div className="od-artifact-tabs" role="tablist">
        {tabs.map((id) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? "is-on" : undefined}
            onClick={() => setTab(id)}
          >
            {LABELS[id] ?? id}
          </button>
        ))}
      </div>
      <div className="od-artifact-paper">
        {typeof body === "string" && body ? (
          <pre>{body}</pre>
        ) : (
          <p className="od-artifact-empty">No document for this tab.</p>
        )}
      </div>
    </div>
  );
}
