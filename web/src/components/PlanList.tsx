import type { MissionStep, MissionStepStatus } from "../lib/demo-data";

const MARK: Record<MissionStepStatus, string> = {
  pending: "·",
  running: "›",
  done: "✓",
  skipped: "–",
  blocked: "→",
  failed: "✕",
};

type Props = {
  steps: MissionStep[];
  tick?: string | null;
};

export default function PlanList({ steps, tick }: Props) {
  return (
    <div className="od-plan">
      {tick ? <p className="od-plan-tick">{tick}</p> : null}
      <ol className="od-plan-list">
        {steps.map((step, i) => (
          <li key={`${step.label}-${i}`} className={`is-${step.status}`}>
            <span className="od-plan-mark" aria-hidden="true">
              {MARK[step.status]}
            </span>
            <div>
              <p className="od-plan-label">{step.label}</p>
              {step.detail ? <p className="od-plan-evidence">{step.detail}</p> : null}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
