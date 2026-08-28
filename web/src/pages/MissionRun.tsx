import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useOutletContext, useParams } from "react-router-dom";
import type { BoardOutlet } from "../components/AppShell";
import ArtifactPane from "../components/ArtifactPane";
import PlanList from "../components/PlanList";
import {
  ACME_ID,
  ACME_STEPS,
  artifacts,
  type Mission,
  type MissionArtifacts,
  type MissionStep,
} from "../lib/demo-data";
import {
  applyEvent,
  eventTick,
  getMission,
  isSeedMission,
  toArtifacts,
  toMission,
  type RunEvent,
  type ServerMission,
} from "../lib/missions-api";

const TICKS: Record<number, string> = {
  0: "Found the 2pm event.",
  1: "Read 6 emails.",
  6: "Drafted agenda. Not sent.",
};

const INTERVAL_MS = 105;

function resetForReplay(): MissionStep[] {
  return ACME_STEPS.map((s, i) =>
    i < 7 ? { ...s, status: "pending" as const } : { ...s, status: "blocked" as const }
  );
}

export default function MissionRun() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { missions, replaceMission, applyServer, openReceipt } = useOutletContext<BoardOutlet>();
  const seedMission = missions.find((m) => m.id === id);
  const seed = isSeedMission(id);
  const [live, setLive] = useState<Mission | null>(null);
  const [liveArts, setLiveArts] = useState<MissionArtifacts | undefined>(undefined);
  const [tick, setTick] = useState<string | null>(null);
  const [replaying, setReplaying] = useState(false);
  const [logOpen, setLogOpen] = useState(false);
  const cancel = useRef(false);

  useEffect(() => {
    return () => {
      cancel.current = true;
    };
  }, []);

  useEffect(() => {
    if (!id || seed) return;
    let closed = false;
    let es: EventSource | null = null;
    void (async () => {
      const res = await getMission(id);
      if (closed) return;
      if (res.status === 401) {
        navigate("/sign-in?next=/desk");
        return;
      }
      if (!res.ok) {
        setLive(null);
        return;
      }
      const raw = (await res.json()) as ServerMission;
      if (closed) return;
      applyServer(raw);
      setLive(toMission(raw));
      setLiveArts(toArtifacts(raw));
      es = new EventSource(`/missions/${id}/events`, { withCredentials: true });
      es.onmessage = (e) => {
        let ev: RunEvent;
        try {
          ev = JSON.parse(e.data) as RunEvent;
        } catch {
          return;
        }
        const nextTick = eventTick(ev);
        if (nextTick) setTick(nextTick);
        setLive((prev) => (prev ? applyEvent(prev, ev) : prev));
        if (
          ev.type === "mission.waiting_on_you" ||
          ev.type === "mission.done" ||
          ev.type === "mission.failed"
        ) {
          es?.close();
          void getMission(id).then(async (r) => {
            if (!r.ok) return;
            const body = (await r.json()) as ServerMission;
            applyServer(body);
            setLive(toMission(body));
            setLiveArts(toArtifacts(body));
          });
        }
      };
    })();
    return () => {
      closed = true;
      es?.close();
    };
  }, [id, seed, applyServer, navigate]);

  const current: Mission | undefined = seed ? seedMission : live ?? seedMission;
  if (!current) {
    return (
      <p className="od-placeholder-body">
        That mission is not on this desk. <Link to="/desk">Missions</Link>
      </p>
    );
  }
  const viewed = current;

  const isAcme = viewed.id === ACME_ID;
  const isFailed = viewed.status === "failed" && seed;

  async function replay() {
    if (!isAcme || replaying) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      replaceMission({
        ...viewed,
        status: "waiting_on_you",
        steps: ACME_STEPS.map((s) => ({ ...s })),
      });
      setTick("Drafted agenda. Not sent.");
      return;
    }

    cancel.current = false;
    setReplaying(true);
    setTick(null);
    let next: Mission = {
      ...viewed,
      status: "running",
      steps: resetForReplay(),
    };
    replaceMission(next);

    for (let i = 0; i < 7; i++) {
      await new Promise((r) => setTimeout(r, INTERVAL_MS));
      if (cancel.current) {
        setReplaying(false);
        return;
      }
      const steps = next.steps.map((s, idx) =>
        idx === i ? { ...s, status: "done" as const, detail: ACME_STEPS[i].detail } : s
      );
      next = { ...next, steps };
      replaceMission(next);
      if (TICKS[i]) setTick(TICKS[i]);
    }

    next = {
      ...next,
      status: "waiting_on_you",
      steps: ACME_STEPS.map((s) => ({ ...s })),
    };
    replaceMission(next);
    setReplaying(false);
  }

  return (
    <div className="od-run">
      <div className="od-run-head">
        <p className="od-run-kicker">
          <Link to="/desk">Missions</Link>
        </p>
        <h1 className="od-run-intent">{viewed.intent}</h1>
        <div className="od-run-tools">
          {isAcme ? (
            <button type="button" className="od-btn od-btn-ghost" onClick={replay} disabled={replaying}>
              Replay
            </button>
          ) : null}
          <button type="button" className="od-btn od-btn-ghost" onClick={() => openReceipt(viewed.id)}>
            Receipt
          </button>
          {isFailed ? (
            <>
              <button type="button" className="od-btn od-btn-ghost">
                Retry step
              </button>
              <button
                type="button"
                className="od-btn od-btn-ghost"
                onClick={() => setLogOpen((v) => !v)}
              >
                Open log
              </button>
            </>
          ) : null}
        </div>
      </div>

      {logOpen ? (
        <pre className="od-run-log">
          {viewed.steps
            .map((s) => `${s.status}  ${s.label}${s.detail ? ` — ${s.detail}` : ""}`)
            .join("\n")}
        </pre>
      ) : null}

      <div className="od-run-split">
        <PlanList steps={viewed.steps} tick={tick} />
        <ArtifactPane artifacts={seed ? artifacts[viewed.id] : liveArts} />
      </div>
    </div>
  );
}
