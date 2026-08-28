export type StepStatus = "done" | "failed";
export type ReceiptStatus =
  | "running"
  | "completed"
  | "awaiting_approval"
  | "resolved"
  | "partial_failure";

export type ReceiptStep = {
  label: string;
  detail?: string;
  status: StepStatus;
};

export type PendingAction = {
  id: string;
  label: string;
};

export type ResolvedAction = {
  label: string;
  outcome: "approved" | "declined";
};

export type Receipt = {
  id: string;
  intent: string;
  status: ReceiptStatus;
  steps: ReceiptStep[];
  pending_actions: PendingAction[];
  resolved_actions: ResolvedAction[];
  tools_used: string[];
  execution_time_seconds: number;
  estimated_minutes_saved: number;
  unauthorized_actions?: number;
  legal?: string;
  footer_ctas?: string[];
  created_at: string;
};

export type Artifact = {
  title: string;
  kind: "brief" | "agenda" | "followup" | "note";
  body: string;
};

export type Goal = {
  id: string;
  receipt_id: string;
  intent: string;
  status: ReceiptStatus;
  created_at: string;
  live_trace: string[];
  artifacts: Artifact[];
};

export type Integration = {
  id: string;
  name: string;
  role: string;
  connected: boolean;
  status: string;
  required_for: string;
};

export type MemoryItem = {
  id: string;
  layer: "user" | "project" | "execution";
  title: string;
  body: string;
  receipt_id?: string;
  updated_at: string;
};

export type DeskState = {
  goals: Goal[];
  receipts: Receipt[];
  integrations: Integration[];
  memory: MemoryItem[];
  next_receipt_seq: number;
  time_saved_minutes: number;
};
