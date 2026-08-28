"""Policy: automate the work, confirm the consequences."""

CONSEQUENTIAL = {
    "send_email",
    "send-agenda",
    "share_document",
    "delete",
    "modify_important_event",
}


def requires_approval(action_id: str) -> bool:
    return action_id in CONSEQUENTIAL or action_id.startswith("send")
