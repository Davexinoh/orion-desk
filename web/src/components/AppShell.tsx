import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import ApprovalBar from "./ApprovalBar";
import CommandBar from "./CommandBar";
import ReceiptDrawer from "./ReceiptDrawer";
import {
  ACME_ID,
  approvals as seedApprovals,
  artifacts as seedArtifacts,
  missions as seedMissions,
  receiptForMission,
  type Mission,
  type MissionArtifacts,
  type PendingApproval,
} from "../lib/demo-data";
import { useAuth } from "../lib/AuthContext";
import {
  isDemoBoardId,
  isForbiddenSeedCard,
  isSeedMission,
  listApprovals,
  listMissions,
  postApprovalDo,
  postApprovalDraft,
  postMission,
  toApprovals,
  toArtifacts,
  toMission,
  toPendingApproval,
  toReceipt,
  type ServerApproval,
  type ServerMission,
} from "../lib/missions-api";
import type { Receipt } from "../lib/types";

type BoardState = { missions: Mission[]; pending: PendingApproval[] };

function cloneSeed(): BoardState {
  return {
    missions: seedMissions.map((m) => ({ ...m, steps: m.steps.map((s) => ({ ...s })) })),
    pending: seedApprovals.map((p) => ({ ...p })),
  };
}

function acmeArtifactMap(): Record<string, MissionArtifacts> {
  const arts = seedArtifacts[ACME_ID];
  return arts ? { [ACME_ID]: arts } : {};
}

const rail = [
  { to: "/desk", label: "Missions", end: true },
  { to: "/desk/approvals", label: "Approvals" },
  { to: "/desk/receipts", label: "Receipts" },
  { to: "/desk/memory", label: "Memory" },
  { to: "/desk/settings", label: "Settings" },
];

const mobileNav = rail.filter((l) => l.label !== "Settings");

function CompassMark() {
  return (
    <svg
      className="od-compass"
      width="18"
      height="18"
      viewBox="0 0 18 18"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M9 1.5L10.35 7.65L16.5 9L10.35 10.35L9 16.5L7.65 10.35L1.5 9L7.65 7.65Z"
        stroke="currentColor"
        strokeWidth="1.15"
        strokeLinejoin="miter"
      />
    </svg>
  );
}

export type BoardOutlet = {
  missions: Mission[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onFillCommand: (intent: string) => void;
  pending: PendingApproval[];
  artifactsById: Record<string, MissionArtifacts>;
  receiptsById: Record<string, Receipt>;
  doIt: (id: string) => void;
  keepDraft: (id: string) => void;
  replaceMission: (mission: Mission) => void;
  applyServer: (raw: ServerMission) => void;
  openReceipt: (id: string) => void;
  resetDemo: () => void;
};

function isTypingTarget(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
}

export default function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const commandRef = useRef<HTMLInputElement>(null);
  const isPublicAcme = location.pathname.replace(/\/+$/, "") === `/desk/m/${ACME_ID}`;
  const boardScope = isPublicAcme ? "public-acme" : user?.userId ?? "public";
  const [command, setCommand] = useState("");
  const [missions, setMissions] = useState<Mission[]>(() =>
    isPublicAcme ? cloneSeed().missions : []
  );
  const [pending, setPending] = useState<PendingApproval[]>(() =>
    isPublicAcme ? cloneSeed().pending : []
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [receiptsById, setReceiptsById] = useState<Record<string, Receipt>>({});
  const [artifactsById, setArtifactsById] = useState<Record<string, MissionArtifacts>>(() =>
    isPublicAcme ? acmeArtifactMap() : {}
  );
  const posting = useRef(false);
  const liveLoad = useRef(0);

  const applyLiveMissions = useCallback((rows: ServerMission[]) => {
    const live = rows.filter((raw) => !isForbiddenSeedCard(raw));
    setMissions((prev) => {
      const fromServer = live.map(toMission);
      const extras = prev.filter(
        (m) => !isDemoBoardId(m.id) && !fromServer.some((s) => s.id === m.id)
      );
      return [...extras, ...fromServer];
    });
    setReceiptsById((prev) => {
      const next: Record<string, Receipt> = {};
      for (const [id, receipt] of Object.entries(prev)) {
        if (!isDemoBoardId(id)) next[id] = receipt;
      }
      for (const raw of live) {
        const receipt = toReceipt(raw);
        if (receipt) next[raw.id] = receipt;
      }
      return next;
    });
    setArtifactsById((prev) => {
      const next: Record<string, MissionArtifacts> = {};
      for (const [id, arts] of Object.entries(prev)) {
        if (!isDemoBoardId(id)) next[id] = arts;
      }
      for (const raw of live) {
        const arts = toArtifacts(raw);
        if (arts) next[raw.id] = arts;
      }
      return next;
    });
  }, []);

  const loadLive = useCallback(async () => {
    const gen = ++liveLoad.current;
    const [mRes, aRes] = await Promise.all([listMissions(), listApprovals()]);
    if (gen !== liveLoad.current) return;
    if (mRes.status === 401 || aRes.status === 401) {
      navigate("/sign-in?next=/desk");
      return;
    }
    if (mRes.ok) {
      const body = (await mRes.json()) as { missions?: ServerMission[] };
      applyLiveMissions(body.missions || []);
    }
    if (aRes.ok) {
      const body = (await aRes.json()) as { approvals?: ServerApproval[] };
      const fromServer = (body.approvals || [])
        .map((a) => toPendingApproval(a))
        .filter((p) => !isDemoBoardId(p.mission_id));
      setPending((prev) => {
        const extras = prev.filter(
          (p) => !isDemoBoardId(p.mission_id) && !fromServer.some((s) => s.id === p.id)
        );
        return [...extras, ...fromServer];
      });
    }
  }, [applyLiveMissions, navigate]);

  useEffect(() => {
    setSelectedId(null);
    setCommand("");
    if (isPublicAcme) {
      liveLoad.current += 1;
      const board = cloneSeed();
      setMissions(board.missions);
      setPending(board.pending);
      setReceiptsById({});
      setArtifactsById(acmeArtifactMap());
      return;
    }
    liveLoad.current += 1;
    setMissions([]);
    setPending([]);
    setReceiptsById({});
    setArtifactsById({});
    if (!user?.userId) return;
    void loadLive();
  }, [boardScope, isPublicAcme, loadLive, user?.userId]);

  const deskPending = isPublicAcme
    ? pending
    : pending.filter((p) => !isDemoBoardId(p.mission_id));
  const approvalCount = deskPending.length;
  const selected =
    missions.find((m) => m.id === selectedId) ??
    (selectedId && isSeedMission(selectedId)
      ? seedMissions.find((m) => m.id === selectedId) ?? null
      : null);
  const isMissions = location.pathname === "/desk";
  const runMatch = location.pathname.match(/^\/desk\/m\/([^/]+)/);
  const runId = runMatch?.[1] ?? null;

  const applyServer = useCallback((raw: ServerMission) => {
    if (isForbiddenSeedCard(raw)) return;
    const mapped = toMission(raw);
    const nextPending = toApprovals(raw);
    setMissions((prev) => {
      const rest = prev.filter((m) => m.id !== mapped.id && !isForbiddenSeedCard(m));
      return [mapped, ...rest];
    });
    setPending((prev) => {
      const others = prev.filter(
        (p) => p.mission_id !== mapped.id && !isDemoBoardId(p.mission_id)
      );
      return [...nextPending, ...others];
    });
    const receipt = toReceipt(raw);
    if (receipt) {
      setReceiptsById((prev) => ({ ...prev, [mapped.id]: receipt }));
    }
    const arts = toArtifacts(raw);
    if (arts) {
      setArtifactsById((prev) => ({ ...prev, [mapped.id]: arts }));
    }
  }, []);

  function doIt(id: string) {
    const row = pending.find((p) => p.id === id);
    if (!row) return;
    if (isSeedMission(row.mission_id)) {
      setPending((prev) => prev.filter((p) => p.id !== id));
      setMissions((prev) =>
        prev.map((m) =>
          m.id === row.mission_id
            ? {
                ...m,
                status: "done",
                steps: m.steps.map((s) =>
                  s.status === "blocked" ? { ...s, status: "done" as const } : s
                ),
              }
            : m
        )
      );
      return;
    }
    void (async () => {
      const res = await postApprovalDo(row.id);
      if (res.status === 401) {
        navigate("/sign-in?next=/desk");
        return;
      }
      if (!res.ok) return;
      const raw = (await res.json()) as ServerMission;
      applyServer(raw);
    })();
  }

  function keepDraft(id: string) {
    const row = pending.find((p) => p.id === id);
    if (!row || isSeedMission(row.mission_id)) return;
    void (async () => {
      const res = await postApprovalDraft(row.id);
      if (res.status === 401) {
        navigate("/sign-in?next=/desk");
        return;
      }
      if (!res.ok) return;
      const raw = (await res.json()) as ServerMission;
      applyServer(raw);
    })();
  }

  const barRow = useMemo(() => {
    if (runId) return deskPending.find((p) => p.mission_id === runId) ?? null;
    if (selectedId) return deskPending.find((p) => p.mission_id === selectedId) ?? null;
    if (isMissions) return deskPending[0] ?? null;
    return null;
  }, [deskPending, selectedId, runId, isMissions]);

  const showBar = Boolean(barRow) && (isMissions || Boolean(runId) || Boolean(selected));

  function submitCommand() {
    const intent = command.trim();
    if (!intent || posting.current) return;
    if (!user) {
      navigate("/sign-in?next=/desk");
      return;
    }
    posting.current = true;
    void (async () => {
      try {
        const res = await postMission(intent);
        if (res.status === 401) {
          navigate("/sign-in?next=/desk");
          return;
        }
        if (!res.ok) return;
        const raw = (await res.json()) as ServerMission;
        applyServer(raw);
        setCommand("");
        navigate(`/desk/m/${raw.id}`);
      } finally {
        posting.current = false;
      }
    })();
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setSelectedId(null);
        window.dispatchEvent(new Event("od-escape"));
        return;
      }
      if (isTypingTarget(e.target)) return;
      if (e.key === "/" && isMissions) {
        e.preventDefault();
        commandRef.current?.focus();
        return;
      }
      if (e.key === "a" || e.key === "A") {
        e.preventDefault();
        navigate("/desk/approvals");
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isMissions, navigate]);

  const outlet: BoardOutlet = {
    missions,
    selectedId,
    onSelect: setSelectedId,
    onFillCommand: setCommand,
    pending: deskPending,
    artifactsById,
    receiptsById,
    doIt,
    keepDraft,
    replaceMission: (mission) => {
      setMissions((prev) => prev.map((m) => (m.id === mission.id ? mission : m)));
    },
    applyServer,
    openReceipt: setSelectedId,
    resetDemo: () => {
      setSelectedId(null);
      setCommand("");
      if (isPublicAcme) {
        const fresh = cloneSeed();
        setMissions(fresh.missions);
        setPending(fresh.pending);
        setReceiptsById({});
        setArtifactsById(acmeArtifactMap());
        return;
      }
      setMissions([]);
      setPending([]);
      setReceiptsById({});
      setArtifactsById({});
      if (user?.userId) void loadLive();
    },
  };

  return (
    <div className="od-app-shell">
      <header className="od-top">
        <div className="od-top-inner">
          <NavLink to="/desk" className="wordmark" end>
            <CompassMark />
            Orion <span>Desk</span>
          </NavLink>
          {user ? (
            <Link className="od-session-name" to="/desk/settings">
              {user.displayName}
            </Link>
          ) : (
            <Link className="od-session-name" to="/sign-in">
              Sign in
            </Link>
          )}
        </div>
      </header>

      <CommandBar
        ref={commandRef}
        value={command}
        onChange={setCommand}
        onSubmit={submitCommand}
      />

      <div className="od-app-body">
        <nav className="od-rail" aria-label="Desk">
          {rail.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              aria-current={
                l.label === "Missions" && (isMissions || Boolean(runId))
                  ? "page"
                  : undefined
              }
            >
              <span>{l.label}</span>
              {l.label === "Approvals" && approvalCount > 0 ? (
                <span className="od-rail-badge">{approvalCount}</span>
              ) : null}
            </NavLink>
          ))}
        </nav>

        <main className="od-canvas">
          <Outlet context={outlet} />
        </main>
      </div>

      {showBar && barRow ? (
        <ApprovalBar
          label={barRow.bar_label}
          onDoIt={() => doIt(barRow.id)}
          onKeep={() => keepDraft(barRow.id)}
        />
      ) : null}

      <nav className="od-mobile-nav" aria-label="Desk">
        {mobileNav.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}>
            {l.label}
            {l.label === "Approvals" && approvalCount > 0 ? ` ${approvalCount}` : ""}
          </NavLink>
        ))}
      </nav>

      <ReceiptDrawer
        open={Boolean(selected)}
        receipt={
          selected ? receiptsById[selected.id] ?? receiptForMission(selected) : null
        }
        onClose={() => setSelectedId(null)}
        onDoIt={
          barRow && selected && barRow.mission_id === selected.id
            ? () => doIt(barRow.id)
            : undefined
        }
        onKeep={
          barRow && selected && barRow.mission_id === selected.id
            ? () => keepDraft(barRow.id)
            : undefined
        }
      />
    </div>
  );
}
