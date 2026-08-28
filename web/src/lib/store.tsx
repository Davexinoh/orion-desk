import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { apiDecide, apiStartGoal, apiStream } from "./api";
import { DEFAULT_INTEGRATIONS, SEED_MEMORY } from "./demo";
import { resolveAction, runLocalGoal } from "./engine";
import type { DeskState, Goal, Receipt } from "./types";

type Toast = { id: number; text: string } | null;

type Store = {
  state: DeskState;
  toast: Toast;
  runningId: string | null;
  liveTrace: Record<string, string>;
  startGoal: (intent: string) => Promise<Goal>;
  approve: (receiptId: string, actionId: string) => void;
  decline: (receiptId: string, actionId: string) => void;
  receiptById: (id: string) => Receipt | undefined;
  goalById: (id: string) => Goal | undefined;
  dismissToast: () => void;
};

const Ctx = createContext<Store | null>(null);

const initial: DeskState = {
  goals: [],
  receipts: [],
  integrations: DEFAULT_INTEGRATIONS,
  memory: SEED_MEMORY,
  next_receipt_seq: 1,
  time_saved_minutes: 0,
};

export function DeskProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DeskState>(initial);
  const [toast, setToast] = useState<Toast>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [liveTrace, setLiveTrace] = useState<Record<string, string>>({});
  const seq = useRef(1);
  const cancel = useRef({ cancelled: false });
  const streams = useRef<Record<string, () => void>>({});

  useEffect(() => {
    fetch("/api/state")
      .then((r) => (r.ok ? r.json() : null))
      .then((snap: DeskState | null) => {
        if (!snap || !Array.isArray(snap.goals)) return;
        setState((prev) => ({
          ...prev,
          ...snap,
          integrations: snap.integrations?.length ? snap.integrations : prev.integrations,
          memory: snap.memory?.length ? snap.memory : prev.memory,
        }));
      })
      .catch(() => {
        /* frontend-only demo */
      });
    return () => {
      Object.values(streams.current).forEach((stop) => stop());
    };
  }, []);

  const show = useCallback((text: string) => {
    const id = Date.now();
    setToast({ id, text });
    window.setTimeout(() => {
      setToast((t) => (t && t.id === id ? null : t));
    }, 3200);
  }, []);

  const startGoal = useCallback(
    async (intent: string) => {
      const remote = await apiStartGoal(intent);
      if (remote) {
        setState((prev) => ({
          ...prev,
          goals: [remote, ...prev.goals.filter((g) => g.id !== remote.id)],
        }));
        setRunningId(remote.id);
        streams.current[remote.id]?.();
        streams.current[remote.id] = apiStream(remote.id, (ev) => {
          if (ev.trace && ev.receipt) {
            setLiveTrace((t) => ({ ...t, [ev.receipt!.id]: ev.trace as string }));
          }
          setState((prev) => {
            const receipt = ev.receipt;
            const goal = ev.goal ?? prev.goals.find((g) => g.id === remote.id);
            const goals = goal
              ? [goal, ...prev.goals.filter((g) => g.id !== goal.id)]
              : prev.goals;
            const receipts = receipt
              ? [receipt, ...prev.receipts.filter((r) => r.id !== receipt.id)]
              : prev.receipts;
            return { ...prev, goals, receipts };
          });
          if (ev.receipt && ev.receipt.status !== "running") {
            setRunningId(null);
            if (ev.receipt.status === "awaiting_approval") {
              show("One thing needs your OK before I send it.");
            } else if (ev.receipt.status === "completed" || ev.receipt.status === "resolved") {
              show("Done. Here's everything I did.");
            }
          }
        });
        return remote;
      }

      const n = seq.current++;
      const created_at = new Date().toISOString();
      const placeholderId = `g-${n}`;
      const goal: Goal = {
        id: placeholderId,
        receipt_id: "",
        intent,
        status: "running",
        created_at,
        live_trace: [],
        artifacts: [],
      };

      setState((prev) => ({
        ...prev,
        goals: [goal, ...prev.goals],
        next_receipt_seq: n + 1,
      }));
      setRunningId(placeholderId);

      void runLocalGoal(
        n,
        intent,
        (receipt, trace, artifacts) => {
          setState((prev) => {
            const goals = prev.goals.map((g) =>
              g.id === placeholderId
                ? {
                    ...g,
                    receipt_id: receipt.id,
                    status: receipt.status,
                    live_trace:
                      g.live_trace[g.live_trace.length - 1] === trace
                        ? g.live_trace
                        : [...g.live_trace, trace],
                    artifacts: artifacts ?? g.artifacts,
                  }
                : g
            );
            const receipts = prev.receipts.some((r) => r.id === receipt.id)
              ? prev.receipts.map((r) => (r.id === receipt.id ? receipt : r))
              : [receipt, ...prev.receipts];
            return { ...prev, goals, receipts };
          });
          setLiveTrace((t) => ({ ...t, [receipt.id]: trace }));
        },
        cancel.current
      ).then((finished) => {
        setState((prev) => ({
          ...prev,
          time_saved_minutes:
            prev.time_saved_minutes + (finished.estimated_minutes_saved || 0),
        }));
        setRunningId(null);
        if (finished.status === "awaiting_approval") {
          show("One thing needs your OK before I send it.");
        } else {
          show("Done. Here's everything I did.");
        }
      }).catch(() => {
        setRunningId(null);
        show("Couldn't finish that run. Try again.");
      });

      return goal;
    },
    [show]
  );

  const approve = useCallback(
    (receiptId: string, actionId: string) => {
      void apiDecide(receiptId, actionId, "approved").then((remote) => {
        if (!remote) return;
        setState((prev) => ({
          ...prev,
          receipts: prev.receipts.map((r) => (r.id === receiptId ? remote : r)),
          goals: prev.goals.map((g) =>
            g.receipt_id === receiptId ? { ...g, status: remote.status } : g
          ),
        }));
      });
      setState((prev) => {
        const current = prev.receipts.find((r) => r.id === receiptId);
        if (!current) return prev;
        const next = resolveAction(current, actionId, "approved");
        return {
          ...prev,
          receipts: prev.receipts.map((r) => (r.id === receiptId ? next : r)),
          goals: prev.goals.map((g) =>
            g.receipt_id === receiptId ? { ...g, status: next.status } : g
          ),
          memory: [
            {
              id: `ex-${Date.now()}`,
              layer: "execution",
              title: `Receipt ${receiptId}`,
              body: next.resolved_actions[next.resolved_actions.length - 1]?.label ?? "Action approved.",
              receipt_id: receiptId,
              updated_at: new Date().toISOString(),
            },
            ...prev.memory,
          ],
        };
      });
      show("Sent. The receipt is closed.");
    },
    [show]
  );

  const decline = useCallback(
    (receiptId: string, actionId: string) => {
      void apiDecide(receiptId, actionId, "declined").then((remote) => {
        if (!remote) return;
        setState((prev) => ({
          ...prev,
          receipts: prev.receipts.map((r) => (r.id === receiptId ? remote : r)),
          goals: prev.goals.map((g) =>
            g.receipt_id === receiptId ? { ...g, status: remote.status } : g
          ),
        }));
      });
      setState((prev) => {
        const current = prev.receipts.find((r) => r.id === receiptId);
        if (!current) return prev;
        const next = resolveAction(current, actionId, "declined");
        return {
          ...prev,
          receipts: prev.receipts.map((r) => (r.id === receiptId ? next : r)),
          goals: prev.goals.map((g) =>
            g.receipt_id === receiptId ? { ...g, status: next.status } : g
          ),
          memory: [
            {
              id: `ex-${Date.now()}`,
              layer: "execution",
              title: `Receipt ${receiptId}`,
              body: next.resolved_actions[next.resolved_actions.length - 1]?.label ?? "Action declined.",
              receipt_id: receiptId,
              updated_at: new Date().toISOString(),
            },
            ...prev.memory,
          ],
        };
      });
      show("Held. Nothing went out.");
    },
    [show]
  );

  const receiptById = useCallback(
    (id: string) => state.receipts.find((r) => r.id === id || r.id === `#${id}`),
    [state.receipts]
  );

  const goalById = useCallback(
    (id: string) => state.goals.find((g) => g.id === id || g.receipt_id === id || g.receipt_id === `#${id}`),
    [state.goals]
  );

  const value = useMemo<Store>(
    () => ({
      state,
      toast,
      runningId,
      liveTrace,
      startGoal,
      approve,
      decline,
      receiptById,
      goalById,
      dismissToast: () => setToast(null),
    }),
    [state, toast, runningId, liveTrace, startGoal, approve, decline, receiptById, goalById]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useDesk() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useDesk must be used inside DeskProvider");
  return ctx;
}
