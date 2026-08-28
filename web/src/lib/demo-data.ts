import type { Receipt, ReceiptStep } from "./types";

export type MissionStatus =
  | "running"
  | "waiting_on_you"
  | "done"
  | "draft"
  | "idle"
  | "failed";

export type MissionStepStatus = "pending" | "running" | "done" | "skipped" | "blocked" | "failed";

export type MissionStep = {
  label: string;
  status: MissionStepStatus;
  detail?: string;
};

export type Mission = {
  id: string;
  intent: string;
  status: MissionStatus;
  steps: MissionStep[];
  tools: string[];
  started_label: string;
  elapsed_seconds?: number;
  minutes_not_spent?: number;
  waiting_for_input?: boolean;
};

export type PendingApproval = {
  id: string;
  mission_id: string;
  action_id: string;
  verb_object: string;
  bar_label: string;
  parent_intent: string;
  age: string;
  risk: string;
};

export type MissionArtifacts = {
  brief: string;
  agenda: string;
  calendar: string;
  followUp: string;
  attendees: string[];
};

export type MemoryFact = {
  id: string;
  text: string;
  receipt_id?: string;
};

export type MemoryGroup = {
  id: string;
  title: string;
  facts: MemoryFact[];
};

export type MemorySeed = {
  user: MemoryFact[];
  project: MemoryGroup[];
  execution: MemoryFact[];
};

export type DemoStats = {
  actions: number;
  integrations: number;
  elapsed: string;
  notSpent: string;
  unauthorized: number;
};

export const ACME_ID = "acme-0491";

export const ACME_EXAMPLE =
  "I have a meeting with Acme tomorrow at 2 PM. I haven't prepared anything. Handle it.";

export const EMPTY_EXAMPLES = [
  "Turn these notes into a client update and a task list.",
  "What in my inbox is waiting on me this week.",
  "I have a meeting with Acme tomorrow at 2 PM. Handle it.",
] as const;

export const ACME_ATTENDEES = ["Jane", "Mark", "Priya", "Dan"] as const;

export const ACME_STEPS: MissionStep[] = [
  {
    label: "Calendar inspected",
    status: "done",
    detail: "Found event: Acme / Tomorrow 14:00",
  },
  {
    label: "Email history analyzed",
    status: "done",
    detail: "6 previous emails read",
  },
  {
    label: "Documents retrieved",
    status: "done",
    detail: "2 relevant documents reviewed",
  },
  {
    label: "External research completed",
    status: "done",
    detail: "Company researched",
  },
  { label: "Meeting briefing generated", status: "done" },
  { label: "Preparation block scheduled", status: "done" },
  { label: "Follow-up drafted", status: "done" },
  { label: "Send agenda to attendees", status: "blocked" },
];

export const missions: Mission[] = [
  {
    id: ACME_ID,
    intent: ACME_EXAMPLE,
    status: "waiting_on_you",
    steps: ACME_STEPS,
    tools: ["Calendar", "Gmail", "Drive", "Web"],
    started_label: "9:12",
    elapsed_seconds: 42,
    minutes_not_spent: 47,
  },
  {
    id: "q2-benchmarks",
    intent: "Research Q2 benchmarks",
    status: "done",
    steps: [
      { label: "Scope pulled", status: "done" },
      { label: "Sources listed", status: "done" },
      { label: "Figures compared", status: "done" },
      { label: "Notes filed", status: "done" },
      { label: "Summary written", status: "done" },
      { label: "Shared to Drive", status: "done" },
    ],
    tools: ["Web", "Drive"],
    started_label: "8:04",
    minutes_not_spent: 72,
  },
  {
    id: "investor-update",
    intent: "Draft investor update",
    status: "draft",
    steps: [
      { label: "Outline", status: "done" },
      { label: "Numbers in", status: "done" },
      { label: "Narrative", status: "pending" },
      { label: "Risks", status: "pending" },
      { label: "Ask", status: "pending" },
      { label: "Send", status: "pending" },
    ],
    tools: ["Drive", "Gmail"],
    started_label: "Yesterday",
  },
  {
    id: "pricing-feedback",
    intent: "Sync pricing feedback",
    status: "idle",
    steps: [
      { label: "Collect notes", status: "pending" },
      { label: "Cluster themes", status: "pending" },
      { label: "Draft reply", status: "pending" },
      { label: "Send", status: "pending" },
    ],
    tools: ["Gmail"],
    started_label: "—",
    waiting_for_input: true,
  },
  {
    id: "failed-0502",
    intent: "Pull last week’s invoices and send the reminder.",
    status: "failed",
    steps: [
      { label: "Locate invoice folder", status: "done" },
      { label: "Gmail search failed", status: "failed", detail: "couldn't verify credentials" },
      { label: "Send reminder", status: "blocked" },
    ],
    tools: ["Drive", "Gmail"],
    started_label: "Yesterday",
    elapsed_seconds: 11,
  },
];

export const artifacts: Record<string, MissionArtifacts> = {
  [ACME_ID]: {
    brief: `Acme — tomorrow 14:00
Jane, Mark, Priya, Dan

They are deciding the 200-seat expansion. Proposal v3 is current. Open: pricing, unsigned DPA, SOC 2, pilot end date.

Lead with the pricing table. Do not reopen scope.`,
    agenda: `Agenda — Acme, tomorrow 2:00 PM

1. Pilot status
2. Open commercial points
3. Legal / DPA / SOC 2
4. Pilot end date
5. Owners and next steps

Not sent.`,
    calendar: "Prep block tomorrow 13:15–13:45",
    followUp: `Subject: Recap — Acme expansion review

Jane, Mark, Priya, Dan —

Notes from today, then owners.

Not sent.`,
    attendees: [...ACME_ATTENDEES],
  },
};

export const receipts: Record<string, Receipt> = {
  [ACME_ID]: {
    id: "#0491",
    intent: ACME_EXAMPLE,
    status: "awaiting_approval",
    steps: ACME_STEPS
      .filter((s) => s.status === "done")
      .map(
        (s): ReceiptStep => ({
          label: s.label,
          detail: s.detail,
          status: "done",
        })
      ),
    pending_actions: [{ id: "send-agenda", label: "Send agenda to 4 attendees" }],
    resolved_actions: [],
    tools_used: ["Calendar", "Gmail", "Drive", "Web"],
    execution_time_seconds: 42,
    estimated_minutes_saved: 47,
    unauthorized_actions: 0,
    legal: "Desk does not send external messages without approval.",
    created_at: "2026-08-27T09:12:00Z",
  },
  "q2-benchmarks": {
    id: "#0490",
    intent: "Research Q2 benchmarks",
    status: "completed",
    steps: [
      { label: "Scope pulled", status: "done" },
      { label: "Sources listed", status: "done" },
      { label: "Figures compared", status: "done" },
      { label: "Notes filed", status: "done" },
      { label: "Summary written", status: "done" },
      { label: "Shared to Drive", status: "done" },
    ],
    pending_actions: [],
    resolved_actions: [],
    tools_used: ["Web", "Drive"],
    execution_time_seconds: 68,
    estimated_minutes_saved: 72,
    unauthorized_actions: 0,
    legal: "Desk does not send external messages without approval.",
    created_at: "2026-08-27T08:04:00Z",
  },
  "investor-update": {
    id: "#0488",
    intent: "Draft investor update",
    status: "running",
    steps: [
      { label: "Outline", status: "done" },
      { label: "Numbers in", status: "done" },
    ],
    pending_actions: [],
    resolved_actions: [],
    tools_used: ["Drive", "Gmail"],
    execution_time_seconds: 0,
    estimated_minutes_saved: 0,
    unauthorized_actions: 0,
    legal: "Desk does not send external messages without approval.",
    created_at: "2026-08-26T16:00:00Z",
  },
  "pricing-feedback": {
    id: "#0487",
    intent: "Sync pricing feedback",
    status: "running",
    steps: [],
    pending_actions: [],
    resolved_actions: [],
    tools_used: ["Gmail"],
    execution_time_seconds: 0,
    estimated_minutes_saved: 0,
    unauthorized_actions: 0,
    legal: "Desk does not send external messages without approval.",
    created_at: "2026-08-26T12:00:00Z",
  },
  "failed-0502": {
    id: "#0502",
    intent: "Pull last week’s invoices and send the reminder.",
    status: "partial_failure",
    steps: [
      { label: "Locate invoice folder", status: "done" },
      {
        label: "Gmail search failed",
        detail: "couldn't verify credentials",
        status: "failed",
      },
    ],
    pending_actions: [],
    resolved_actions: [],
    tools_used: ["Drive", "Gmail"],
    execution_time_seconds: 11,
    estimated_minutes_saved: 0,
    unauthorized_actions: 0,
    legal: "Desk does not send external messages without approval.",
    footer_ctas: ["Retry step", "Open log"],
    created_at: "2026-08-26T18:40:00Z",
  },
};

export const approvals: PendingApproval[] = [
  {
    id: "ap-acme-agenda",
    mission_id: ACME_ID,
    action_id: "send-agenda",
    verb_object: "Send agenda to Jane, Mark, Priya, Dan",
    bar_label: "Send agenda to 4 attendees",
    parent_intent: ACME_EXAMPLE,
    age: "3m ago",
    risk: "External send",
  },
];

export const memory: MemorySeed = {
  user: [
    { id: "u1", text: "Keep emails concise" },
    { id: "u2", text: "No meetings before 10:00" },
    { id: "u3", text: "Agendas in bullets" },
  ],
  project: [
    {
      id: "p-acme",
      title: "Acme",
      facts: [
        { id: "a1", text: "Current proposal: v3" },
        { id: "a2", text: "Previous meetings: last call recap filed" },
        { id: "a3", text: "Outstanding issues: pricing, DPA, SOC 2, pilot end" },
        { id: "a4", text: "Relevant documents: proposal v3, last call notes" },
        { id: "a5", text: "Deadlines: pilot end still open" },
      ],
    },
    {
      id: "p-q2",
      title: "Q2 planning",
      facts: [
        { id: "q1", text: "Benchmark pack filed" },
        { id: "q2", text: "Compare against last year, not last quarter" },
        { id: "q3", text: "Web + Drive already pulled" },
      ],
    },
    {
      id: "p-inv",
      title: "Investors",
      facts: [
        { id: "i1", text: "Update in draft" },
        { id: "i2", text: "Numbers in; narrative not" },
        { id: "i3", text: "Ask still empty" },
      ],
    },
  ],
  execution: [
    { id: "e1", text: "Agenda created yesterday · user kept as draft", receipt_id: "#0491" },
    { id: "e2", text: "Prep block placed tomorrow 13:15–13:45" },
    { id: "e3", text: "Brief generated for Acme" },
    { id: "e4", text: "Follow-up drafted. Not sent." },
    { id: "e5", text: "Q2 benchmark pack filed" },
  ],
};

export const demoStats: DemoStats = {
  actions: 8,
  integrations: 5,
  elapsed: "43 seconds",
  notSpent: "~47 minutes",
  unauthorized: 0,
};

export function receiptForMission(mission: Mission): Receipt {
  const base = receipts[mission.id];
  if (mission.id === ACME_ID) {
    const waiting = mission.status === "waiting_on_you";
    const seed = receipts[ACME_ID];
    if (waiting) return seed;
    return {
      ...seed,
      status: "resolved",
      pending_actions: [],
      resolved_actions: [{ label: "Agenda sent to 4 attendees", outcome: "approved" }],
    };
  }
  if (base) return base;
  return {
    id: "#0000",
    intent: mission.intent,
    status: "running",
    steps: mission.steps
      .filter((s) => s.status === "done")
      .map((s) => ({ label: s.label, detail: s.detail, status: "done" as const })),
    pending_actions: [],
    resolved_actions: [],
    tools_used: mission.tools,
    execution_time_seconds: mission.elapsed_seconds ?? 0,
    estimated_minutes_saved: mission.minutes_not_spent ?? 0,
    unauthorized_actions: 0,
    legal: "Desk does not send external messages without approval.",
    created_at: new Date().toISOString(),
  };
}

/** @deprecated use missions */
export const SEED_MISSIONS = missions;
/** @deprecated use approvals */
export const SEED_APPROVALS = approvals;
