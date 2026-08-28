import type { Mission, MissionArtifacts, MissionStep, MissionStepStatus, PendingApproval } from "./demo-data";
import type { Receipt } from "./types";

export const SEED_IDS = new Set(["acme-0491", "failed-0502"]);

export function isSeedMission(id: string | undefined): boolean {
  return Boolean(id && SEED_IDS.has(id));
}

export type ServerMission = {
  id: string;
  intent: string;
  status: string;
  steps: Array<{
    label: string;
    state?: string;
    status?: string;
    evidence?: string | null;
    detail?: string | null;
    index?: number;
  }>;
  tools?: string[];
  started_label?: string;
  elapsed_seconds?: number;
  minutes_not_spent?: number | null;
  receipt?: Receipt | null;
  artifacts?: Array<{ kind: string; body: string }>;
  approvals?: Array<{
    id: string;
    mission_id?: string;
    missionId?: string;
    action_id?: string;
    verb_object?: string;
    verbObject?: string;
    bar_label?: string;
    parent_intent?: string;
    age?: string;
    risk?: string;
    status?: string;
  }>;
};

const STEP_STATUS: Record<string, MissionStepStatus> = {
  pending: "pending",
  running: "running",
  done: "done",
  skipped: "skipped",
  blocked: "blocked",
  failed: "failed",
};

function stepStatus(raw: string | undefined): MissionStepStatus {
  return STEP_STATUS[raw || ""] ?? "pending";
}

export function toMission(raw: ServerMission): Mission {
  const rawStatus = raw.status || "running";
  const status = (rawStatus === "queued" ? "running" : rawStatus) as Mission["status"];
  return {
    id: raw.id,
    intent: raw.intent,
    status,
    steps: (raw.steps || []).map(
      (s): MissionStep => ({
        label: s.label,
        status: stepStatus(s.state || s.status),
        detail: s.evidence || s.detail || undefined,
      })
    ),
    tools: raw.tools || [],
    started_label: raw.started_label || "—",
    elapsed_seconds: raw.elapsed_seconds,
    minutes_not_spent: raw.minutes_not_spent ?? undefined,
    waiting_for_input: raw.status === "waiting_on_you",
  };
}

export function toApprovals(raw: ServerMission): PendingApproval[] {
  return (raw.approvals || [])
    .filter((a) => a.status === "needed")
    .map((a) => ({
      id: a.id,
      mission_id: a.mission_id || a.missionId || raw.id,
      action_id: a.action_id || a.id,
      verb_object: a.verb_object || a.verbObject || "",
      bar_label: a.bar_label || a.verbObject || a.verb_object || "",
      parent_intent: a.parent_intent || raw.intent,
      age: a.age || "now",
      risk: a.risk || "External send",
    }));
}

export function toArtifacts(raw: ServerMission): MissionArtifacts | undefined {
  const list = raw.artifacts || [];
  if (!list.length) return undefined;
  const out: MissionArtifacts = { brief: "", agenda: "", calendar: "", followUp: "", attendees: [] };
  for (const a of list) {
    if (a.kind === "brief" || a.kind === "agenda" || a.kind === "calendar" || a.kind === "followUp") {
      out[a.kind] = a.body;
    }
  }
  return out;
}

export function toReceipt(raw: ServerMission): Receipt | null {
  return raw.receipt ?? null;
}

export async function postMission(intent: string): Promise<Response> {
  return fetch("/missions", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intent }),
  });
}

export async function getMission(id: string): Promise<Response> {
  return fetch(`/missions/${id}`, { credentials: "include" });
}

export async function postApprovalDo(id: string): Promise<Response> {
  return fetch(`/approvals/${id}/do`, { method: "POST", credentials: "include" });
}

export async function postApprovalDraft(id: string): Promise<Response> {
  return fetch(`/approvals/${id}/draft`, { method: "POST", credentials: "include" });
}

export type RunEvent = {
  type: string;
  stepIndex?: number;
  label?: string;
  evidence?: string;
  reason?: string;
};

export function applyEvent(mission: Mission, ev: RunEvent): Mission {
  const steps = mission.steps.map((s) => ({ ...s }));
  const idx = typeof ev.stepIndex === "number" ? ev.stepIndex - 1 : -1;
  if (idx >= 0 && idx < steps.length) {
    if (ev.type === "step.running") steps[idx] = { ...steps[idx], status: "running" };
    if (ev.type === "step.done") {
      steps[idx] = { ...steps[idx], status: "done", detail: ev.evidence || steps[idx].detail };
    }
    if (ev.type === "step.blocked") {
      steps[idx] = { ...steps[idx], status: "blocked", detail: ev.reason || steps[idx].detail };
    }
    if (ev.type === "step.failed") {
      steps[idx] = { ...steps[idx], status: "failed", detail: ev.evidence || steps[idx].detail };
    }
  }
  let status = mission.status;
  if (ev.type === "mission.waiting_on_you") status = "waiting_on_you";
  if (ev.type === "mission.done") status = "done";
  if (ev.type === "mission.failed") status = "failed";
  if (ev.type === "mission.started") status = "running";
  return { ...mission, steps, status };
}

export function eventTick(ev: RunEvent): string | null {
  if (ev.type === "step.done" && ev.evidence) return ev.evidence;
  if (ev.type === "step.running" && ev.label) return ev.label;
  if (ev.type === "step.blocked") return ev.reason || "Needs approval.";
  if (ev.type === "step.failed" && ev.evidence) return ev.evidence;
  return null;
}
