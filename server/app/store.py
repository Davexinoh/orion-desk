from __future__ import annotations

import asyncio
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .demo_data import INTEGRATIONS, SEED_MEMORY

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "state.json"

Listener = Callable[[dict], None]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.state: dict[str, Any] = {
            "goals": [],
            "receipts": [],
            "integrations": copy.deepcopy(INTEGRATIONS),
            "memory": copy.deepcopy(SEED_MEMORY),
            "next_receipt_seq": 1,
            "time_saved_minutes": 0,
        }
        self._listeners: dict[str, list[asyncio.Queue]] = {}
        self.load()

    def load(self) -> None:
        if DATA_PATH.exists():
            try:
                self.state = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

    def persist(self) -> None:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def snapshot(self) -> dict:
        return copy.deepcopy(self.state)

    def next_seq(self) -> int:
        n = int(self.state.get("next_receipt_seq") or 1)
        self.state["next_receipt_seq"] = n + 1
        return n

    def upsert_goal(self, goal: dict) -> None:
        goals = self.state["goals"]
        for i, g in enumerate(goals):
            if g["id"] == goal["id"]:
                goals[i] = goal
                return
        goals.insert(0, goal)

    def upsert_receipt(self, receipt: dict) -> None:
        receipts = self.state["receipts"]
        for i, r in enumerate(receipts):
            if r["id"] == receipt["id"]:
                receipts[i] = receipt
                return
        receipts.insert(0, receipt)

    def get_receipt(self, rid: str) -> dict | None:
        rid_n = rid if rid.startswith("#") else f"#{rid}"
        for r in self.state["receipts"]:
            if r["id"] in (rid, rid_n, rid.lstrip("#")):
                return r
        return None

    def get_goal(self, gid: str) -> dict | None:
        for g in self.state["goals"]:
            if g["id"] == gid or g.get("receipt_id") == gid:
                return g
        return None

    def add_memory(self, item: dict) -> None:
        self.state["memory"].insert(0, item)

    def subscribe(self, receipt_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._listeners.setdefault(receipt_id, []).append(q)
        return q

    def unsubscribe(self, receipt_id: str, q: asyncio.Queue) -> None:
        lst = self._listeners.get(receipt_id) or []
        if q in lst:
            lst.remove(q)

    async def publish(self, receipt_id: str, event: dict) -> None:
        for q in list(self._listeners.get(receipt_id) or []):
            await q.put(event)


STORE = Store()
