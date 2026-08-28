from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DATA = Path(__file__).resolve().parent.parent / "data" / "email_tokens.json"
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
TTL = 15 * 60
EMAIL_COOLDOWN = 60
IP_HOUR = 60 * 60
IP_HOUR_LIMIT = 5


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def mail_configured() -> bool:
    if not (os.getenv("MAIL_FROM") or "").strip():
        return False
    return bool((os.getenv("SMTP_HOST") or os.getenv("SMTP_URL") or "").strip())


def _origin() -> str:
    return (os.getenv("APP_ORIGIN") or "http://127.0.0.1:5173").rstrip("/")


def magic_body(token: str) -> str:
    origin = _origin()
    return (
        "Orion Desk\n\n"
        "Open this desk:\n"
        f"{origin}/auth/email/callback?token={token}\n\n"
        "This link expires in 15 minutes.\n"
        "If you did not ask for it, ignore this.\n"
    )


def send_magic_mail(to: str, token: str) -> None:
    from_addr = (os.getenv("MAIL_FROM") or "").strip()
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = "Orion Desk"
    msg.set_content(magic_body(token))

    smtp_url = (os.getenv("SMTP_URL") or "").strip()
    host = (os.getenv("SMTP_HOST") or "").strip()
    port = int(os.getenv("SMTP_PORT") or "587")
    user = os.getenv("SMTP_USER") or ""
    password = os.getenv("SMTP_PASS") or ""
    use_tls = (os.getenv("SMTP_TLS") or "1") != "0"

    if smtp_url:
        parsed = urlparse(smtp_url)
        host = parsed.hostname or host
        port = parsed.port or (465 if parsed.scheme == "smtps" else port)
        user = parsed.username or user
        password = parsed.password or password
        use_tls = parsed.scheme != "smtp"

    if not host:
        raise RuntimeError("no smtp host")

    if port == 465:
        smtp: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=12)
    else:
        smtp = smtplib.SMTP(host, port, timeout=12)
    try:
        if use_tls and port != 465:
            smtp.starttls()
        if user:
            smtp.login(user, password)
        smtp.send_message(msg)
    finally:
        smtp.quit()


class EmailAuth:
    def __init__(self) -> None:
        self.tokens: list[dict[str, Any]] = []
        self.email_last: dict[str, float] = {}
        self.ip_sends: dict[str, list[float]] = {}
        self.load()

    def load(self) -> None:
        if not DATA.exists():
            return
        try:
            raw = json.loads(DATA.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        self.tokens = raw.get("tokens") or []
        self.email_last = {k: float(v) for k, v in (raw.get("email_last") or {}).items()}
        self.ip_sends = {k: [float(t) for t in v] for k, v in (raw.get("ip_sends") or {}).items()}

    def persist(self) -> None:
        now = time.time()
        self.tokens = [
            t
            for t in self.tokens
            if not t.get("used") and float(t.get("exp") or 0) > now
        ]
        DATA.parent.mkdir(parents=True, exist_ok=True)
        DATA.write_text(
            json.dumps(
                {
                    "tokens": self.tokens,
                    "email_last": self.email_last,
                    "ip_sends": self.ip_sends,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _rate_ok(self, email: str, ip: str) -> bool:
        now = time.time()
        last = self.email_last.get(email) or 0
        if now - last < EMAIL_COOLDOWN:
            return False
        stamps = [t for t in self.ip_sends.get(ip, []) if now - t < IP_HOUR]
        self.ip_sends[ip] = stamps
        if len(stamps) >= IP_HOUR_LIMIT:
            return False
        return True

    def _mark_sent(self, email: str, ip: str) -> None:
        now = time.time()
        self.email_last[email] = now
        stamps = [t for t in self.ip_sends.get(ip, []) if now - t < IP_HOUR]
        stamps.append(now)
        self.ip_sends[ip] = stamps

    def start(self, email: str, ip: str, next_path: str, local: bool) -> dict:
        addr = normalize_email(email)
        if not valid_email(addr):
            raise ValueError("invalid")
        if not self._rate_ok(addr, ip):
            raise PermissionError("rate")
        token = secrets.token_urlsafe(32)
        self.tokens.append(
            {
                "hash": hash_token(token),
                "email": addr,
                "exp": time.time() + TTL,
                "used": False,
                "next": next_path,
            }
        )
        self._mark_sent(addr, ip)
        self.persist()
        if mail_configured():
            send_magic_mail(addr, token)
            return {"ok": True}
        if local:
            return {"ok": True, "devLink": f"/auth/email/callback?token={token}"}
        raise RuntimeError("no mail")

    def consume(self, raw: str) -> tuple[str, str] | None:
        if not raw:
            return None
        digest = hash_token(raw)
        now = time.time()
        for row in self.tokens:
            stored = str(row.get("hash") or "")
            if len(stored) != len(digest) or not hmac.compare_digest(stored, digest):
                continue
            if row.get("used"):
                return None
            if float(row.get("exp") or 0) < now:
                row["used"] = True
                self.persist()
                return None
            row["used"] = True
            self.persist()
            email = str(row.get("email") or "")
            nxt = str(row.get("next") or "/desk")
            if not email:
                return None
            return email, nxt
        return None


EMAIL = EmailAuth()
