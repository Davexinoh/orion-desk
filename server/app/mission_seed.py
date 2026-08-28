from __future__ import annotations

ACME_ID = "acme-0491"
FAILED_ID = "failed-0502"
PUBLIC_IDS = frozenset({ACME_ID, FAILED_ID})

ACME_INTENT = (
    "I have a meeting with Acme tomorrow at 2 PM. I haven't prepared anything. Handle it."
)
LEGAL = "Desk does not send external messages without approval."

ACME = {
    "id": ACME_ID,
    "userId": None,
    "intent": ACME_INTENT,
    "status": "waiting_on_you",
    "toolNames": [
        "calendar.read",
        "gmail.search",
        "drive.read",
        "web.search",
        "doc.draft",
        "calendar.write",
        "gmail.send",
    ],
    "tools": ["Calendar", "Gmail", "Drive", "Web"],
    "startedAt": "2026-08-27T09:12:00Z",
    "started_label": "9:12",
    "elapsedMs": 42000,
    "notSpentMinutes": 47,
    "unauthorized": 0,
    "steps": [
        {
            "id": "acme-0491-s1",
            "index": 1,
            "label": "Calendar inspected",
            "state": "done",
            "evidence": "Found event: Acme / Tomorrow 14:00",
            "tool": "calendar.read",
        },
        {
            "id": "acme-0491-s2",
            "index": 2,
            "label": "Email history analyzed",
            "state": "done",
            "evidence": "6 previous emails read",
            "tool": "gmail.search",
        },
        {
            "id": "acme-0491-s3",
            "index": 3,
            "label": "Documents retrieved",
            "state": "done",
            "evidence": "2 relevant documents reviewed",
            "tool": "drive.read",
        },
        {
            "id": "acme-0491-s4",
            "index": 4,
            "label": "External research completed",
            "state": "done",
            "evidence": "Company researched",
            "tool": "web.search",
        },
        {
            "id": "acme-0491-s5",
            "index": 5,
            "label": "Meeting briefing generated",
            "state": "done",
            "evidence": None,
            "tool": "doc.draft",
        },
        {
            "id": "acme-0491-s6",
            "index": 6,
            "label": "Preparation block scheduled",
            "state": "done",
            "evidence": None,
            "tool": "calendar.write",
        },
        {
            "id": "acme-0491-s7",
            "index": 7,
            "label": "Follow-up drafted",
            "state": "done",
            "evidence": None,
            "tool": "doc.draft",
        },
        {
            "id": "acme-0491-s8",
            "index": 8,
            "label": "Send agenda to attendees",
            "state": "blocked",
            "evidence": None,
            "tool": "gmail.send",
        },
    ],
    "artifacts": [
        {
            "kind": "brief",
            "title": "Acme brief",
            "body": (
                "Acme — tomorrow 14:00\n"
                "Jane, Mark, Priya, Dan\n\n"
                "They are deciding the 200-seat expansion. Proposal v3 is current. "
                "Open: pricing, unsigned DPA, SOC 2, pilot end date.\n\n"
                "Lead with the pricing table. Do not reopen scope."
            ),
            "sent": False,
        },
        {
            "kind": "agenda",
            "title": "Agenda — Acme, tomorrow 2:00 PM",
            "body": (
                "Agenda — Acme, tomorrow 2:00 PM\n\n"
                "1. Pilot status\n"
                "2. Open commercial points\n"
                "3. Legal / DPA / SOC 2\n"
                "4. Pilot end date\n"
                "5. Owners and next steps\n\n"
                "Not sent."
            ),
            "sent": False,
        },
        {
            "kind": "calendar",
            "title": "Prep block",
            "body": "Prep block tomorrow 13:15–13:45",
            "sent": False,
        },
        {
            "kind": "followUp",
            "title": "Follow-up",
            "body": (
                "Subject: Recap — Acme expansion review\n\n"
                "Jane, Mark, Priya, Dan —\n\n"
                "Notes from today, then owners.\n\n"
                "Not sent."
            ),
            "sent": False,
        },
    ],
    "receipt": {
        "id": "#0491",
        "intent": ACME_INTENT,
        "status": "awaiting_approval",
        "steps": [
            {"label": "Calendar inspected", "detail": "Found event: Acme / Tomorrow 14:00", "status": "done"},
            {"label": "Email history analyzed", "detail": "6 previous emails read", "status": "done"},
            {"label": "Documents retrieved", "detail": "2 relevant documents reviewed", "status": "done"},
            {"label": "External research completed", "detail": "Company researched", "status": "done"},
            {"label": "Meeting briefing generated", "status": "done"},
            {"label": "Preparation block scheduled", "status": "done"},
            {"label": "Follow-up drafted", "status": "done"},
        ],
        "pending_actions": [{"id": "send-agenda", "label": "Send agenda to 4 attendees"}],
        "resolved_actions": [],
        "tools_used": ["Calendar", "Gmail", "Drive", "Web"],
        "execution_time_seconds": 42,
        "estimated_minutes_saved": 47,
        "unauthorized_actions": 0,
        "legal": LEGAL,
        "created_at": "2026-08-27T09:12:00Z",
    },
    "approvals": [
        {
            "id": "ap-acme-agenda",
            "userId": None,
            "verbObject": "Send agenda to Jane, Mark, Priya, Dan",
            "risk": "External send",
            "artifactKind": "agenda",
            "status": "needed",
            "action_id": "send-agenda",
            "bar_label": "Send agenda to 4 attendees",
            "parent_intent": ACME_INTENT,
            "age": "3m ago",
        }
    ],
}

FAILED = {
    "id": FAILED_ID,
    "userId": None,
    "intent": "Pull last week’s invoices and send the reminder.",
    "status": "failed",
    "toolNames": ["drive.read", "gmail.search", "gmail.send"],
    "tools": ["Drive", "Gmail"],
    "startedAt": "2026-08-26T18:40:00Z",
    "started_label": "Yesterday",
    "elapsedMs": 11000,
    "notSpentMinutes": 0,
    "unauthorized": 0,
    "steps": [
        {
            "id": "failed-0502-s1",
            "index": 1,
            "label": "Locate invoice folder",
            "state": "done",
            "evidence": None,
            "tool": "drive.read",
        },
        {
            "id": "failed-0502-s2",
            "index": 2,
            "label": "Gmail search failed",
            "state": "failed",
            "evidence": "couldn't verify credentials",
            "tool": "gmail.search",
        },
        {
            "id": "failed-0502-s3",
            "index": 3,
            "label": "Send reminder",
            "state": "blocked",
            "evidence": None,
            "tool": "gmail.send",
        },
    ],
    "artifacts": [],
    "receipt": {
        "id": "#0502",
        "intent": "Pull last week’s invoices and send the reminder.",
        "status": "partial_failure",
        "steps": [
            {"label": "Locate invoice folder", "status": "done"},
            {
                "label": "Gmail search failed",
                "detail": "couldn't verify credentials",
                "status": "failed",
            },
        ],
        "pending_actions": [],
        "resolved_actions": [],
        "tools_used": ["Drive", "Gmail"],
        "execution_time_seconds": 11,
        "estimated_minutes_saved": 0,
        "unauthorized_actions": 0,
        "legal": LEGAL,
        "footer_ctas": ["Retry step", "Open log"],
        "created_at": "2026-08-26T18:40:00Z",
    },
    "approvals": [],
}
