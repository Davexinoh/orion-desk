from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from .mission_seed import ACME, FAILED, PUBLIC_IDS

DB = Path(__file__).resolve().parent.parent / "data" / "orion.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS missions (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  intent TEXT NOT NULL,
  status TEXT NOT NULL,
  tool_names TEXT NOT NULL,
  tools TEXT NOT NULL,
  started_at TEXT,
  started_label TEXT,
  elapsed_ms INTEGER NOT NULL DEFAULT 0,
  not_spent_minutes INTEGER,
  unauthorized INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS steps (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  idx INTEGER NOT NULL,
  label TEXT NOT NULL,
  state TEXT NOT NULL,
  evidence TEXT,
  tool TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
  mission_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  sent INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (mission_id, kind)
);
CREATE TABLE IF NOT EXISTS receipts (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL UNIQUE,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  user_id TEXT,
  verb_object TEXT NOT NULL,
  risk TEXT NOT NULL,
  artifact_kind TEXT,
  status TEXT NOT NULL,
  action_id TEXT,
  bar_label TEXT,
  parent_intent TEXT,
  age TEXT
);
"""


class MissionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        DB.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(DB, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()
            self._seed_public()

    def _seed_public(self) -> None:
        for row in (ACME, FAILED):
            if self._get_mission(row["id"]):
                continue
            self._insert_bundle(row)

    def _insert_bundle(self, bundle: dict[str, Any]) -> None:
        m = bundle
        self._conn.execute(
            """
            INSERT INTO missions (
              id, user_id, intent, status, tool_names, tools,
              started_at, started_label, elapsed_ms, not_spent_minutes, unauthorized
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                m["id"],
                m.get("userId"),
                m["intent"],
                m["status"],
                json.dumps(m.get("toolNames") or []),
                json.dumps(m.get("tools") or []),
                m.get("startedAt"),
                m.get("started_label"),
                int(m.get("elapsedMs") or 0),
                m.get("notSpentMinutes"),
                int(m.get("unauthorized") or 0),
            ),
        )
        for step in m.get("steps") or []:
            self._conn.execute(
                """
                INSERT INTO steps (id, mission_id, idx, label, state, evidence, tool)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step["id"],
                    m["id"],
                    step["index"],
                    step["label"],
                    step["state"],
                    step.get("evidence"),
                    step.get("tool"),
                ),
            )
        for art in m.get("artifacts") or []:
            self._conn.execute(
                """
                INSERT INTO artifacts (mission_id, kind, title, body, sent)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    m["id"],
                    art["kind"],
                    art["title"],
                    art["body"],
                    1 if art.get("sent") else 0,
                ),
            )
        receipt = m.get("receipt")
        if receipt:
            self._conn.execute(
                "INSERT INTO receipts (id, mission_id, payload) VALUES (?, ?, ?)",
                (receipt["id"], m["id"], json.dumps(receipt)),
            )
        for ap in m.get("approvals") or []:
            self._conn.execute(
                """
                INSERT INTO approvals (
                  id, mission_id, user_id, verb_object, risk, artifact_kind,
                  status, action_id, bar_label, parent_intent, age
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ap["id"],
                    m["id"],
                    ap.get("userId"),
                    ap["verbObject"],
                    ap["risk"],
                    ap.get("artifactKind"),
                    ap["status"],
                    ap.get("action_id"),
                    ap.get("bar_label"),
                    ap.get("parent_intent"),
                    ap.get("age"),
                ),
            )
        self._conn.commit()

    def _get_mission(self, mission_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM missions WHERE id = ?", (mission_id,)
        ).fetchone()

    def get(self, mission_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._get_mission(mission_id)
            if not row:
                return None
            steps = self._conn.execute(
                "SELECT * FROM steps WHERE mission_id = ? ORDER BY idx", (mission_id,)
            ).fetchall()
            arts = self._conn.execute(
                "SELECT * FROM artifacts WHERE mission_id = ?", (mission_id,)
            ).fetchall()
            receipt_row = self._conn.execute(
                "SELECT payload FROM receipts WHERE mission_id = ?", (mission_id,)
            ).fetchone()
            approvals = self._conn.execute(
                "SELECT * FROM approvals WHERE mission_id = ?", (mission_id,)
            ).fetchall()
            return public_mission(row, steps, arts, receipt_row, approvals)

    def exists(self, mission_id: str) -> bool:
        with self._lock:
            return self._get_mission(mission_id) is not None

    def _refuse_public(self, mission_id: str) -> None:
        if mission_id in PUBLIC_IDS:
            raise ValueError("public seed is read-only")

    def create(self, bundle: dict[str, Any]) -> None:
        mid = bundle["id"]
        self._refuse_public(mid)
        if mid in PUBLIC_IDS:
            raise ValueError("public seed is read-only")
        with self._lock:
            if self._get_mission(mid):
                raise ValueError("mission exists")
            self._insert_bundle(
                {
                    **bundle,
                    "artifacts": bundle.get("artifacts") or [],
                    "receipt": bundle.get("receipt"),
                    "approvals": bundle.get("approvals") or [],
                }
            )

    def set_step(self, mission_id: str, index: int, state: str, evidence: str | None) -> None:
        self._refuse_public(mission_id)
        with self._lock:
            self._conn.execute(
                "UPDATE steps SET state = ?, evidence = ? WHERE mission_id = ? AND idx = ?",
                (state, evidence, mission_id, index),
            )
            self._conn.commit()

    def set_status(self, mission_id: str, status: str, elapsed_ms: int) -> None:
        self._refuse_public(mission_id)
        with self._lock:
            self._conn.execute(
                "UPDATE missions SET status = ?, elapsed_ms = ? WHERE id = ?",
                (status, elapsed_ms, mission_id),
            )
            self._conn.commit()

    def upsert_artifact(self, mission_id: str, art: dict[str, Any]) -> None:
        self._refuse_public(mission_id)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO artifacts (mission_id, kind, title, body, sent)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(mission_id, kind) DO UPDATE SET
                  title = excluded.title,
                  body = excluded.body,
                  sent = excluded.sent
                """,
                (
                    mission_id,
                    art["kind"],
                    art["title"],
                    art["body"],
                    1 if art.get("sent") else 0,
                ),
            )
            self._conn.commit()

    def add_approval(self, ap: dict[str, Any]) -> None:
        mission_id = ap.get("missionId") or ap.get("mission_id")
        if not mission_id:
            # runner passes id without mission_id; infer from approval id prefix after create
            raise ValueError("mission id required")
        self._refuse_public(mission_id)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO approvals (
                  id, mission_id, user_id, verb_object, risk, artifact_kind,
                  status, action_id, bar_label, parent_intent, age
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ap["id"],
                    mission_id,
                    ap.get("userId"),
                    ap["verbObject"],
                    ap["risk"],
                    ap.get("artifactKind"),
                    ap["status"],
                    ap.get("action_id"),
                    ap.get("bar_label"),
                    ap.get("parent_intent"),
                    ap.get("age"),
                ),
            )
            self._conn.commit()

    def upsert_receipt(self, mission_id: str, receipt: dict[str, Any]) -> None:
        self._refuse_public(mission_id)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO receipts (id, mission_id, payload) VALUES (?, ?, ?)
                ON CONFLICT(mission_id) DO UPDATE SET
                  id = excluded.id,
                  payload = excluded.payload
                """,
                (receipt["id"], mission_id, json.dumps(receipt)),
            )
            self._conn.commit()

    def next_receipt_id(self) -> str:
        with self._lock:
            rows = self._conn.execute("SELECT id FROM receipts").fetchall()
        used: set[int] = set()
        for r in rows:
            raw = str(r["id"]).lstrip("#")
            if raw.isdigit():
                used.add(int(raw))
        n = 1
        while n in used or n in (491, 502):
            n += 1
        return f"#{n:04d}"

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
            if not row:
                return None
            return _approval_row(row)

    def list_needed(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM approvals
                WHERE user_id = ? AND status = 'needed'
                ORDER BY id
                """,
                (user_id,),
            ).fetchall()
            return [_approval_row(r) for r in rows]

    def set_approval_status(self, approval_id: str, status: str) -> None:
        with self._lock:
            row = self._conn.execute(
                "SELECT mission_id FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
            if not row:
                return
            self._refuse_public(row["mission_id"])
            self._conn.execute(
                "UPDATE approvals SET status = ? WHERE id = ?",
                (status, approval_id),
            )
            self._conn.commit()

    def mark_artifact_sent(self, mission_id: str, kind: str) -> None:
        self._refuse_public(mission_id)
        with self._lock:
            self._conn.execute(
                "UPDATE artifacts SET sent = 1 WHERE mission_id = ? AND kind = ?",
                (mission_id, kind),
            )
            self._conn.commit()

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        if not user_id:
            return []
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id FROM missions
                WHERE user_id = ?
                  AND user_id IS NOT NULL
                  AND user_id != ''
                  AND id NOT IN ('acme-0491', 'failed-0502')
                ORDER BY started_at DESC
                """,
                (user_id,),
            ).fetchall()
            ids = [r["id"] for r in rows]
        out = []
        for mid in ids:
            if mid in PUBLIC_IDS:
                continue
            item = self.get(mid)
            if item and item.get("userId") == user_id and item.get("id") not in PUBLIC_IDS:
                out.append(item)
        return out


def _approval_row(ap: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": ap["id"],
        "missionId": ap["mission_id"],
        "mission_id": ap["mission_id"],
        "userId": ap["user_id"],
        "verbObject": ap["verb_object"],
        "verb_object": ap["verb_object"],
        "risk": ap["risk"],
        "artifactKind": ap["artifact_kind"],
        "status": ap["status"],
        "action_id": ap["action_id"],
        "bar_label": ap["bar_label"],
        "parent_intent": ap["parent_intent"],
        "age": ap["age"],
    }


def public_mission(
    row: sqlite3.Row,
    steps: list[sqlite3.Row],
    arts: list[sqlite3.Row],
    receipt_row: sqlite3.Row | None,
    approvals: list[sqlite3.Row],
) -> dict[str, Any]:
    ui_steps = []
    for s in steps:
        ui_steps.append(
            {
                "id": s["id"],
                "index": s["idx"],
                "label": s["label"],
                "state": s["state"],
                "status": s["state"],
                "evidence": s["evidence"],
                "detail": s["evidence"],
                "tool": s["tool"],
            }
        )
    elapsed_ms = int(row["elapsed_ms"] or 0)
    not_spent = row["not_spent_minutes"]
    receipt = json.loads(receipt_row["payload"]) if receipt_row else None
    artifacts = [
        {
            "missionId": a["mission_id"],
            "kind": a["kind"],
            "title": a["title"],
            "body": a["body"],
            "sent": False if not a["sent"] else True,
        }
        for a in arts
    ]
    ui_approvals = [
        {
            "id": ap["id"],
            "missionId": ap["mission_id"],
            "mission_id": ap["mission_id"],
            "userId": ap["user_id"],
            "verbObject": ap["verb_object"],
            "verb_object": ap["verb_object"],
            "risk": ap["risk"],
            "artifactKind": ap["artifact_kind"],
            "status": ap["status"],
            "action_id": ap["action_id"],
            "bar_label": ap["bar_label"],
            "parent_intent": ap["parent_intent"],
            "age": ap["age"],
        }
        for ap in approvals
    ]
    return {
        "id": row["id"],
        "userId": row["user_id"],
        "intent": row["intent"],
        "status": row["status"],
        "steps": ui_steps,
        "toolNames": json.loads(row["tool_names"] or "[]"),
        "tools": json.loads(row["tools"] or "[]"),
        "startedAt": row["started_at"],
        "started_label": row["started_label"],
        "elapsedMs": elapsed_ms,
        "elapsed_seconds": elapsed_ms // 1000,
        "notSpentMinutes": not_spent,
        "minutes_not_spent": not_spent,
        "unauthorized": int(row["unauthorized"] or 0),
        "receipt": receipt,
        "artifacts": artifacts,
        "approvals": ui_approvals,
    }


MISSIONS = MissionStore()
PUBLIC_MISSION_IDS = PUBLIC_IDS
