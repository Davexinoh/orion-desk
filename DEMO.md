# Orion Desk — demo script

Open http://127.0.0.1:5173

## 1. Landing

The receipt on the right is live. It streams the Acme run, then waits.

Approve or decline it. Copy around the receipt is casual; the receipt itself stays literal.

## 2. The run

Click **Open the desk** or type:

```
I have a client meeting with Acme tomorrow at 2 PM. I haven't prepared anything. Handle it.
```

Watch:

- Calendar inspected
- Email history analyzed (6 threads)
- Documents retrieved (2 files)
- External research completed
- 4 unresolved issues identified
- Meeting briefing generated
- Preparation block scheduled
- Follow-up drafted

It stops:

```
PENDING APPROVAL
→ Send agenda to 4 attendees        [Approve] [Decline]
```

## 3. Approval

Approve. The pending line becomes:

```
✓ Agenda sent to 4 attendees
```

Footer stays. Summary strip:

`8 actions · 4 integrations · Ns · 47 min estimated manual work avoided · 0 unauthorized actions`

The briefing, agenda, and follow-up are on the same page.

## 4. Elsewhere

- **Receipts** — same component, same words
- **Integrations** — Telegram, Gmail, Calendar, Drive, web, files
- **Memory** — user / project / execution (the approval is logged)

## 5. Telegram (optional)

Set `TELEGRAM_BOT_TOKEN` and restart the server. Same intent, same receipt text, inline Approve / Decline.
