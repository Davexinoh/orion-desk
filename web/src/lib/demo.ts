import type { Artifact, Integration, MemoryItem, Receipt } from "./types";

export const ACME_INTENT =
  "I have a client meeting with Acme tomorrow at 2 PM. I haven't prepared anything. Handle it.";

export const SAMPLE_INTENTS = [
  "Prepare me for my meeting with Acme tomorrow.",
  "Turn these notes into a content calendar and draft this week's posts.",
  "I need to organize my week around these deadlines.",
  "Read these documents, summarize what matters, and prepare questions for tomorrow's call.",
];

export const DEFAULT_INTEGRATIONS: Integration[] = [
  {
    id: "telegram",
    name: "Telegram",
    role: "Primary conversational interface. Goals, files, approvals, receipts.",
    connected: false,
    status: "Add a bot token to go live. Web chat works now.",
    required_for: "Chat from your phone",
  },
  {
    id: "gmail",
    name: "Gmail",
    role: "Search threads, extract deadlines, draft replies. Sending needs approval.",
    connected: false,
    status: "Demo data loaded. Connect Google to use your inbox.",
    required_for: "Email history and sending",
  },
  {
    id: "calendar",
    name: "Google Calendar",
    role: "Inspect events, schedule prep blocks, flag conflicts.",
    connected: false,
    status: "Demo calendar loaded. Connect Google to use your calendar.",
    required_for: "Meetings and scheduling",
  },
  {
    id: "drive",
    name: "Google Drive / Docs",
    role: "Retrieve files, summarize, generate briefs.",
    connected: false,
    status: "Demo files loaded. Connect Google to use your Drive.",
    required_for: "Documents",
  },
  {
    id: "web",
    name: "Web Search",
    role: "Research companies, people, and topics as part of a run — not a standalone search box.",
    connected: true,
    status: "Ready. Uses live search when a key is present; otherwise a local brief.",
    required_for: "External research",
  },
  {
    id: "files",
    name: "File uploads",
    role: "PDFs, notes, screenshots, spreadsheets become context for the run.",
    connected: true,
    status: "Ready on web and Telegram.",
    required_for: "Ad-hoc documents",
  },
];

export const SEED_MEMORY: MemoryItem[] = [
  {
    id: "m1",
    layer: "user",
    title: "Email tone",
    body: "Keep emails concise. No filler openers. Lead with the ask.",
    updated_at: "2026-08-20T09:12:00Z",
  },
  {
    id: "m2",
    layer: "user",
    title: "Scheduling window",
    body: "Never schedule before 10:00 AM local time.",
    updated_at: "2026-08-18T16:40:00Z",
  },
  {
    id: "m3",
    layer: "project",
    title: "Acme",
    body: "Q3 expansion review. Proposal v3 is current. Open: 200-seat pricing, unsigned DPA, SOC 2 evidence, unconfirmed pilot end date.",
    updated_at: "2026-08-26T11:04:00Z",
  },
  {
    id: "m4",
    layer: "execution",
    title: "Last Acme draft",
    body: "Follow-up template prepared. Agenda not sent — waiting on approval.",
    receipt_id: "#00491",
    updated_at: "2026-08-27T08:12:00Z",
  },
];

export type PlannedStep = {
  delay: number;
  label: string;
  detail?: string;
  status: "done" | "failed";
  tool: string;
  trace: string;
};

export const ACME_PLAN: PlannedStep[] = [
  {
    delay: 700,
    label: "Calendar inspected",
    tool: "Calendar",
    trace: "Reading your calendar...",
  },
  {
    delay: 900,
    label: "Email history analyzed",
    detail: "6 threads",
    tool: "Gmail",
    trace: "Searching previous correspondence...",
  },
  {
    delay: 800,
    label: "Documents retrieved",
    detail: "2 files",
    tool: "Drive",
    trace: "Pulling the files that actually matter...",
  },
  {
    delay: 1000,
    label: "External research completed",
    tool: "Web Search",
    trace: "Looking up Acme...",
  },
  {
    delay: 900,
    label: "4 unresolved issues identified",
    tool: "Gmail",
    trace: "Finding what is still open...",
  },
  {
    delay: 1100,
    label: "Meeting briefing generated",
    tool: "Drive",
    trace: "Writing the briefing...",
  },
  {
    delay: 700,
    label: "Preparation block scheduled",
    tool: "Calendar",
    trace: "Holding 1:00–2:00 PM for prep...",
  },
  {
    delay: 800,
    label: "Follow-up drafted",
    tool: "Gmail",
    trace: "Drafting the follow-up. Not sending it.",
  },
].map((s) => ({ ...s, status: "done" as const }));

export const ACME_PENDING = {
  id: "send-agenda",
  label: "Send agenda to 4 attendees",
};

export function emptyReceipt(id: string, intent: string): Receipt {
  return {
    id,
    intent,
    status: "running",
    steps: [],
    pending_actions: [],
    resolved_actions: [],
    tools_used: [],
    execution_time_seconds: 0,
    estimated_minutes_saved: 0,
    created_at: new Date().toISOString(),
  };
}

export const LANDING_RECEIPT_SEED: Receipt = emptyReceipt(
  "#00491",
  "Prepare me for my Acme meeting."
);

export const ACME_ARTIFACTS: Artifact[] = [
  {
    title: "Meeting briefing — Acme Q3 expansion",
    kind: "brief",
    body: `Acme — Q3 expansion review
Tomorrow · 2:00–3:00 PM · Google Meet
Attendees: you · Sarah Chen (VP Ops, Acme) · James Park (Procurement, Acme) · Priya Nair (CS)

What this meeting is
Acme is deciding whether to expand from the 40-seat pilot to 200 seats in Q4. Proposal v3 (Drive) is the live document. They have not signed the DPA. They have not received SOC 2 evidence. Pilot end date is still “TBD” in the last recap.

Unresolved
1. 200-seat pricing — Sarah asked 12 days ago; no written answer.
2. DPA — legal has the draft; Acme has not signed.
3. SOC 2 Type II — James requested the report; it was not attached.
4. Pilot end date — last call left it open.

Recommended stance
Lead with the pricing table. Do not reopen the product scope. Offer a 30-day DPA close and attach SOC 2 in the follow-up, not live. Propose pilot end = 30 Sep.

Talking points
· Expansion is an ops decision, not a product one — they already use the workflow daily.
· 200-seat quote holds if they sign this month.
· Unblocking legal is the critical path, not the deck.`,
  },
  {
    title: "Agenda (draft, unsent)",
    kind: "agenda",
    body: `Subject: Agenda — Acme Q3 expansion review (tomorrow 2 PM)

1. Pilot status (5 min) — usage, open issues
2. 200-seat pricing (15 min) — table from proposal v3
3. Legal / DPA / SOC 2 (15 min) — what we still owe each other
4. Pilot end date (10 min) — propose 30 Sep
5. Next steps and owners (10 min)

Prep block: 1:00–2:00 PM tomorrow (held on your calendar).`,
  },
  {
    title: "Follow-up template (draft, unsent)",
    kind: "followup",
    body: `Subject: Recap — Acme expansion review

Sarah, James —

Notes from today:
· Pricing: 200-seat figure from proposal v3, valid through month-end.
· DPA: we re-sent the draft; please sign this week.
· SOC 2 Type II attached.
· Pilot end: 30 Sep unless you flag otherwise.

I’ll send calendar holds for the legal close. Reply if I missed an owner.

—`,
  },
];
