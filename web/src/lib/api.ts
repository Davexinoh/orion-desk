import type { Goal, Receipt } from "./types";

const API = "";

export async function apiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API}/api/health`, { signal: AbortSignal.timeout(800) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function apiStartGoal(intent: string): Promise<Goal | null> {
  try {
    const res = await fetch(`${API}/api/goals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent, source: "web" }),
      signal: AbortSignal.timeout(1500),
    });
    if (!res.ok) return null;
    return (await res.json()) as Goal;
  } catch {
    return null;
  }
}

export async function apiDecide(
  receiptId: string,
  actionId: string,
  outcome: "approved" | "declined"
): Promise<Receipt | null> {
  const path = outcome === "approved" ? "approve" : "decline";
  try {
    const res = await fetch(`${API}/api/receipts/${encodeURIComponent(receiptId)}/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: actionId }),
    });
    if (!res.ok) return null;
    return (await res.json()) as Receipt;
  } catch {
    return null;
  }
}

export function apiStream(
  goalId: string,
  onEvent: (ev: { type: string; receipt?: Receipt; goal?: Goal; trace?: string }) => void
): () => void {
  const es = new EventSource(`${API}/api/goals/${encodeURIComponent(goalId)}/stream`);
  es.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data));
    } catch {
      /* ignore malformed */
    }
  };
  return () => es.close();
}
