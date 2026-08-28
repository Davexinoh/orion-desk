from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA = Path(__file__).resolve().parent.parent / "data" / "users.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserStore:
    def __init__(self) -> None:
        self.users: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if DATA.exists():
            try:
                raw = json.loads(DATA.read_text(encoding="utf-8"))
                self.users = raw.get("users") or []
            except json.JSONDecodeError:
                self.users = []

    def persist(self) -> None:
        DATA.parent.mkdir(parents=True, exist_ok=True)
        DATA.write_text(json.dumps({"users": self.users}, indent=2), encoding="utf-8")

    def get(self, user_id: str) -> dict | None:
        return next((u for u in self.users if u["id"] == user_id), None)

    def by_telegram(self, telegram_id: str) -> dict | None:
        return next((u for u in self.users if str(u.get("telegramId") or "") == str(telegram_id)), None)

    def by_email(self, email: str) -> dict | None:
        e = email.lower()
        return next((u for u in self.users if (u.get("email") or "").lower() == e), None)

    def public(self, user: dict) -> dict:
        return {
            "userId": user["id"],
            "displayName": user["displayName"],
            "email": user.get("email"),
            "telegramId": user.get("telegramId"),
            "telegramUsername": user.get("telegramUsername"),
        }

    def set_display_name(self, user_id: str, name: str) -> dict | None:
        user = self.get(user_id)
        if not user:
            return None
        cleaned = " ".join((name or "").split())
        if not cleaned:
            return user
        user["displayName"] = cleaned[:80]
        self.persist()
        return user

    def _drop_if_empty(self, donor: dict) -> None:
        if donor.get("email") or donor.get("telegramId"):
            return
        self.users = [u for u in self.users if u["id"] != donor["id"]]

    def _merge_into(self, existing: dict, donor: dict | None) -> None:
        if not donor or donor["id"] == existing["id"]:
            return
        if donor.get("email") and not existing.get("email"):
            existing["email"] = donor["email"]
            donor["email"] = None
        if donor.get("telegramId") and not existing.get("telegramId"):
            existing["telegramId"] = donor["telegramId"]
            existing["telegramUsername"] = donor.get("telegramUsername")
            donor["telegramId"] = None
            donor["telegramUsername"] = None
        self._drop_if_empty(donor)

    def upsert_dev(self) -> dict:
        found = self.get("dev-demo")
        if found:
            placeholder = (found.get("email") or "").lower() == "demo@oriondesk.local"
            if placeholder and not found.get("telegramId"):
                found["email"] = None
                self.persist()
            return found
        user = {
            "id": "dev-demo",
            "displayName": "Demo",
            "email": None,
            "telegramId": None,
            "telegramUsername": None,
            "approvalPolicy": "all_writes",
            "createdAt": _now(),
        }
        self.users.append(user)
        self.persist()
        return user

    def upsert_telegram(
        self,
        telegram_id: str,
        first_name: str | None,
        username: str | None,
        link_user_id: str | None,
    ) -> dict:
        uname = (username or "").lstrip("@") or None
        display = (first_name or "").strip() or (f"@{uname}" if uname else "Desk user")
        tid = str(telegram_id)
        found = self.by_telegram(tid)
        if link_user_id:
            existing = self.get(link_user_id)
            if existing:
                if str(existing.get("telegramId") or "") == tid:
                    existing["telegramUsername"] = uname
                    self.persist()
                    return existing
                if not existing.get("telegramId"):
                    self._merge_into(existing, found)
                    existing["telegramId"] = tid
                    existing["telegramUsername"] = uname
                    self.persist()
                    return existing
                return existing
        if found:
            found["telegramUsername"] = uname
            if first_name and not found.get("displayName"):
                found["displayName"] = display
            self.persist()
            return found
        user = {
            "id": str(uuid4()),
            "displayName": display,
            "email": None,
            "telegramId": tid,
            "telegramUsername": uname,
            "approvalPolicy": "all_writes",
            "createdAt": _now(),
        }
        self.users.append(user)
        self.persist()
        return user

    def upsert_email(self, email: str, link_user_id: str | None) -> dict:
        addr = email.lower().strip()
        local = addr.split("@")[0] or "Desk user"
        found = self.by_email(addr)
        if link_user_id:
            existing = self.get(link_user_id)
            if existing:
                if (existing.get("email") or "").lower() == addr:
                    return existing
                if not existing.get("email"):
                    self._merge_into(existing, found)
                    existing["email"] = addr
                    self.persist()
                    return existing
                return existing
        if found:
            return found
        user = {
            "id": str(uuid4()),
            "displayName": local,
            "email": addr,
            "telegramId": None,
            "telegramUsername": None,
            "approvalPolicy": "all_writes",
            "createdAt": _now(),
        }
        self.users.append(user)
        self.persist()
        return user


USERS = UserStore()
