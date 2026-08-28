import { useState } from "react";
import type { MissionArtifacts } from "../lib/demo-data";

const TABS = [
  { id: "brief", label: "Brief" },
  { id: "agenda", label: "Agenda" },
  { id: "calendar", label: "Calendar" },
  { id: "followUp", label: "Follow-up" },
] as const;

type TabId = (typeof TABS)[number]["id"];

type Props = {
  artifacts?: MissionArtifacts;
};

export default function ArtifactPane({ artifacts }: Props) {
  const [tab, setTab] = useState<TabId>("brief");
  const body = artifacts?.[tab] ?? "";

  return (
    <div className="od-artifacts">
      <div className="od-artifact-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? "is-on" : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
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
