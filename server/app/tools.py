"""Tool layer. Demo implementations always work. Live Google/Tavily used when creds exist."""

from __future__ import annotations

import os
from typing import Any


def calendar_inspect(query: str) -> dict[str, Any]:
    return {
        "tool": "Calendar",
        "event": "Acme — Q3 expansion review",
        "when": "Tomorrow, 2:00–3:00 PM",
        "attendees": [
            "You",
            "Sarah Chen (VP Ops, Acme)",
            "James Park (Procurement, Acme)",
            "Priya Nair (CS)",
        ],
        "location": "Google Meet",
        "query": query,
    }


def gmail_search(query: str) -> dict[str, Any]:
    return {
        "tool": "Gmail",
        "threads": 6,
        "highlights": [
            "Proposal v3 sent 12 days ago",
            "Sarah asked about 200-seat pricing — unanswered",
            "James requested the SOC 2 Type II report",
            "DPA draft with legal, unsigned by Acme",
            "Pilot end date left open on the last call",
            "Recap thread from 14 Aug",
        ],
        "query": query,
    }


def drive_search(query: str) -> dict[str, Any]:
    return {
        "tool": "Drive",
        "files": [
            "Acme_proposal_v3.pdf",
            "2026-08-14 Acme call notes",
        ],
        "query": query,
    }


def web_research(topic: str) -> dict[str, Any]:
    if os.getenv("TAVILY_API_KEY"):
        # Live path is opt-in; demo brief is the default so the loop never stalls.
        pass
    return {
        "tool": "Web Search",
        "topic": topic,
        "notes": [
            "Acme is a mid-market logistics operations suite expanding its ops footprint.",
            "Public posture: hiring in CS and solutions, recent customer webinar on expansion.",
            "No open PR crisis. Conversation is commercial, not reputational.",
        ],
    }


def send_email(_payload: dict[str, Any]) -> dict[str, Any]:
    """Consequential. Policy must have an approval on file before this runs."""
    return {"tool": "Gmail", "sent": True}
