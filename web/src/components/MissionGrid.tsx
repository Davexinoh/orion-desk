import { useEffect, useMemo, useState } from "react";
import { EMPTY_EXAMPLES, type Mission } from "../lib/demo-data";
import MissionCard from "./MissionCard";
import "./MissionGrid.css";

type Filter = "active" | "waiting" | "done";

type Props = {
  missions: Mission[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  onFillCommand?: (intent: string) => void;
};

function isWaiting(m: Mission): boolean {
  return m.status === "waiting_on_you";
}

function isActive(m: Mission): boolean {
  return m.status === "running" || m.status === "draft" || m.status === "idle";
}

function isDone(m: Mission): boolean {
  return m.status === "done" || m.status === "failed";
}

export default function MissionGrid({
  missions,
  selectedId = null,
  onSelect,
  onFillCommand,
}: Props) {
  const [filters, setFilters] = useState<Record<Filter, boolean>>({
    active: true,
    waiting: true,
    done: false,
  });
  const [cursor, setCursor] = useState<string | null>(null);

  function toggle(f: Filter) {
    setFilters((prev) => ({ ...prev, [f]: !prev[f] }));
  }

  const visible = useMemo(() => {
    const any = filters.active || filters.waiting || filters.done;
    if (!any) return [];
    return missions.filter((m) => {
      if (filters.done && isDone(m)) return true;
      if (filters.waiting && isWaiting(m)) return true;
      if (filters.active && isActive(m) && !isDone(m)) return true;
      return false;
    });
  }, [missions, filters]);

  useEffect(() => {
    if (!visible.length) {
      setCursor(null);
      return;
    }
    if (!cursor || !visible.some((m) => m.id === cursor)) {
      setCursor(visible[0].id);
    }
  }, [visible, cursor]);

  useEffect(() => {
    function typing(el: EventTarget | null) {
      if (!(el instanceof HTMLElement)) return false;
      const tag = el.tagName;
      return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
    }
    function onKey(e: KeyboardEvent) {
      if (typing(e.target) || !visible.length) return;
      if (e.key === "j" || e.key === "J") {
        e.preventDefault();
        const i = Math.max(0, visible.findIndex((m) => m.id === cursor));
        const next = visible[Math.min(visible.length - 1, i + 1)];
        if (next) setCursor(next.id);
      }
      if (e.key === "k" || e.key === "K") {
        e.preventDefault();
        const i = Math.max(0, visible.findIndex((m) => m.id === cursor));
        const next = visible[Math.max(0, i - 1)];
        if (next) setCursor(next.id);
      }
      if (e.key === "Enter" && cursor) {
        e.preventDefault();
        onSelect?.(cursor);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [visible, cursor, onSelect]);

  return (
    <div className="od-mission-grid">
      <div className="od-mission-filters" role="toolbar" aria-label="Mission filters">
        <button
          type="button"
          className={filters.active ? "is-on" : undefined}
          onClick={() => toggle("active")}
        >
          Active
        </button>
        <span aria-hidden="true">·</span>
        <button
          type="button"
          className={filters.waiting ? "is-on" : undefined}
          onClick={() => toggle("waiting")}
        >
          Waiting on you
        </button>
        <span aria-hidden="true">·</span>
        <button
          type="button"
          className={filters.done ? "is-on" : undefined}
          onClick={() => toggle("done")}
        >
          Done
        </button>
      </div>

      {visible.length === 0 ? (
        <div className="od-mission-empty">
          <p>State an outcome.</p>
          {EMPTY_EXAMPLES.map((line) => (
            <button
              key={line}
              type="button"
              className="od-empty-example"
              onClick={() => onFillCommand?.(line)}
            >
              {line}
            </button>
          ))}
        </div>
      ) : (
        <div className="od-mission-cols">
          {visible.map((m) => (
            <MissionCard
              key={m.id}
              mission={m}
              selected={cursor === m.id || selectedId === m.id}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
