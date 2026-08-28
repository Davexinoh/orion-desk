import type { Mission, MissionStatus } from "../lib/demo-data";
import "./MissionCard.css";

type Props = {
  mission: Mission;
  selected?: boolean;
  onSelect?: (id: string) => void;
};

const PILL: Record<MissionStatus, string> = {
  running: "Running",
  waiting_on_you: "Waiting on you",
  done: "Done",
  draft: "Draft",
  idle: "Idle",
  failed: "Failed",
};

function notSpent(minutes?: number): string | null {
  if (minutes == null) return null;
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m ? `~${h}h ${m}m not spent` : `~${h}h not spent`;
  }
  return `~${minutes} min not spent`;
}

function metaLine(mission: Mission): string {
  const parts: string[] = [];
  if (mission.started_label && mission.started_label !== "—") {
    parts.push(`Started ${mission.started_label}`);
  }
  if (mission.elapsed_seconds != null) {
    parts.push(`${mission.elapsed_seconds}s`);
  }
  const saved = notSpent(mission.minutes_not_spent);
  if (saved) parts.push(saved);
  if (mission.waiting_for_input) parts.push("Waiting for input");
  return parts.join(" · ");
}

export default function MissionCard({ mission, selected, onSelect }: Props) {
  const stepsDone = mission.steps.filter((s) => s.status === "done").length;
  const stepsTotal = mission.steps.length;
  const pending =
    mission.status === "waiting_on_you" ||
    mission.steps.some((s) => s.status === "blocked");
  const ratio = stepsTotal > 0 ? stepsDone / stepsTotal : 0;

  return (
    <button
      type="button"
      className={`od-mission-card${pending ? " is-pending" : ""}${selected ? " is-selected" : ""}`}
      aria-pressed={selected}
      onClick={() => onSelect?.(mission.id)}
    >
      <div className="od-mission-card-top">
        <p className="od-mission-intent">{mission.intent}</p>
        <span className={`od-status-pill is-${mission.status}`}>
          {PILL[mission.status]}
        </span>
      </div>

      <div className="od-mission-meter">
        <span>
          {stepsDone} of {stepsTotal} steps
        </span>
        <span
          className="od-mission-progress"
          aria-hidden="true"
        >
          <span style={{ width: `${Math.min(100, ratio * 100)}%` }} />
        </span>
      </div>

      <p className="od-mission-tools">
        {mission.tools.length ? mission.tools.join(" · ") : "—"}
      </p>
      <p className="od-mission-meta">{metaLine(mission)}</p>
      {pending ? <p className="od-mission-need">1 action needs you</p> : null}
    </button>
  );
}
