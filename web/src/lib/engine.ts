import { formatReceiptId } from "./format";
import {
  ACME_ARTIFACTS,
  ACME_PENDING,
  ACME_PLAN,
  emptyReceipt,
  type PlannedStep,
} from "./demo";
import type { Artifact, Receipt } from "./types";

function isMeetingPrep(intent: string): boolean {
  const t = intent.toLowerCase();
  return (
    t.includes("meeting") ||
    t.includes("acme") ||
    t.includes("prepare me") ||
    t.includes("brief") ||
    t.includes("call")
  );
}

function genericPlan(intent: string): PlannedStep[] {
  const subject = intent.replace(/[.?!]$/, "").slice(0, 80);
  return [
    {
      delay: 600,
      label: "Intent parsed",
      tool: "Web Search",
      trace: "Figuring out what you actually want...",
      status: "done",
    },
    {
      delay: 800,
      label: "Context gathered",
      tool: "Web Search",
      trace: "Pulling what I can from connected tools...",
      status: "done",
    },
    {
      delay: 900,
      label: "Plan drafted",
      detail: "4 steps",
      tool: "Drive",
      trace: "Breaking it into work I can finish...",
      status: "done",
    },
    {
      delay: 1000,
      label: `Work product generated for “${subject}”`,
      tool: "Drive",
      trace: "Writing the output...",
      status: "done",
    },
  ];
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function runLocalGoal(
  seq: number,
  intent: string,
  onUpdate: (receipt: Receipt, trace: string, artifacts?: Artifact[]) => void,
  signal?: { cancelled: boolean }
): Promise<Receipt> {
  const id = formatReceiptId(seq);
  let receipt = emptyReceipt(id, intent);
  const started = Date.now();
  const meeting = isMeetingPrep(intent);
  const plan = meeting ? ACME_PLAN : genericPlan(intent);
  const tools: string[] = [];

  onUpdate(receipt, "On it.");

  for (const step of plan) {
    if (signal?.cancelled) return receipt;
    onUpdate({ ...receipt, execution_time_seconds: elapsed(started) }, step.trace);
    await sleep(step.delay);
    if (signal?.cancelled) return receipt;
    if (!tools.includes(step.tool)) tools.push(step.tool);
    receipt = {
      ...receipt,
      steps: [...receipt.steps, { label: step.label, detail: step.detail, status: step.status }],
      tools_used: [...tools],
      execution_time_seconds: elapsed(started),
      estimated_minutes_saved: meeting ? 12 + receipt.steps.length * 5 : 8 + receipt.steps.length * 3,
    };
    onUpdate(receipt, step.trace);
  }

  if (meeting) {
    receipt = {
      ...receipt,
      status: "awaiting_approval",
      pending_actions: [{ ...ACME_PENDING }],
      execution_time_seconds: elapsed(started),
      estimated_minutes_saved: 47,
      tools_used: ["Calendar", "Gmail", "Drive", "Web Search"],
    };
    onUpdate(receipt, "One thing needs your OK before I send it.", ACME_ARTIFACTS);
    return receipt;
  }

  receipt = {
    ...receipt,
    status: receipt.steps.some((s) => s.status === "failed") ? "partial_failure" : "completed",
    execution_time_seconds: elapsed(started),
  };
  onUpdate(receipt, "Done. Here's everything I did.");
  return receipt;
}

function elapsed(started: number): number {
  return Math.max(1, Math.round((Date.now() - started) / 1000));
}

export function resolveAction(
  receipt: Receipt,
  actionId: string,
  outcome: "approved" | "declined"
): Receipt {
  const action = receipt.pending_actions.find((a) => a.id === actionId);
  if (!action) return receipt;
  const remaining = receipt.pending_actions.filter((a) => a.id !== actionId);

  // Spec: pending line converts to a completed fact or a declined fact.
  let finalLabel: string;
  if (action.id === "send-agenda") {
    finalLabel =
      outcome === "approved"
        ? "Agenda sent to 4 attendees"
        : "Agenda not sent — declined";
  } else if (outcome === "approved") {
    finalLabel = action.label.replace(/^Send /, "Sent ");
  } else {
    finalLabel = `${action.label} — declined`;
  }

  return {
    ...receipt,
    status: remaining.length ? "awaiting_approval" : "resolved",
    pending_actions: remaining,
    resolved_actions: [...receipt.resolved_actions, { label: finalLabel, outcome }],
  };
}
