

Orion Desk — Agent Runtime Spec

Version: 1.0  
Product: Orion Desk  
Owns: planning, tools, run events, receipts, Do it  
Does not own: colors, nav, marketing, auth providers  
Authority:  
ORION_DESK_UI_MASTER.md wins on UI.  
ORION_DESK_AUTH.md wins on identity.  
This file wins on execution.

The UI already speaks Missions, Steps, Artifacts, Receipts, Approvals.  
The backend must speak that language. Do not invent a second model.

Gate 0 — Read before any engine code

You are not building:

a chatbot API
a multi-agent swarm
an autonomous emailer
a vector-database product
a rewrite of Replay into a spinner with no receipt

You are building:

one Mission runner
a short plan
tools with a policy gate
an event stream the run view already knows how to show
a receipt that is true

Replay stays.  
For Acme public demo, Replay may still play seed ticks.  
For a signed-in user CommandBar submit, the server runs a live mission.

Do it is the only external send.  
If code can send mail, create a calendar event, or share a file without an approval row, the build is wrong.

Gate 1 — Hard bans

Sending email / calendar write / doc share from the planner
LLM “confirming” that money moved or mail sent
Tools not listed in Gate 6
Changing ActionReceipt field names
Replacing PlanList with a raw token stream
New desk routes for “agent console”
Blocking /desk/m/acme-0491 on auth
Calling the model on every keystroke
Storing raw provider API keys in the repo

Gate 2 — Domain objects

Use these names. Map tables to them. Do not rename in the API.

type StepState = "pending" | "running" | "done" | "skipped" | "blocked" | "failed"

type MissionStatus =
  | "draft"
  | "queued"
  | "running"
  | "waiting_on_you"
  | "done"
  | "failed"
  | "idle"

type Mission = {
  id: string
  userId: string | null          // null = public seed
  intent: string
  status: MissionStatus
  steps: Step[]
  toolNames: string[]
  startedAt: string | null
  elapsedMs: number
  notSpentMinutes: number | null
  unauthorized: 0
}

type Step = {
  id: string
  index: number                  // 1-based
  label: string
  state: StepState
  evidence: string | null        // 12px muted line in PlanList
  tool: string | null
}

type ArtifactKind = "brief" | "agenda" | "calendar" | "followUp"

type Artifact = {
  missionId: string
  kind: ArtifactKind
  title: string
  body: string                   // markdown / plain
  sent: false
}

type Receipt = {
  id: string                     // 0491 style
  missionId: string
  intent: string
  done: string[]
  needsYou: string[]
  tools: string[]
  elapsed: string                // "42 seconds"
  notSpent: string               // "~47 minutes"
  unauthorized: 0
  legal: "Desk does not send external messages without approval."
}

type Approval = {
  id: string
  missionId: string
  userId: string
  verbObject: string             // Send agenda to Jane, Mark, Priya, Dan
  risk: "External send" | "Calendar write" | "File share"
  artifactKind: ArtifactKind
  status: "needed" | "approved" | "dismissed"
}

type RunEvent =
  | { type: "mission.started"; missionId: string }
  | { type: "step.running"; stepIndex: number; label: string }
  | { type: "step.done"; stepIndex: number; evidence: string }
  | { type: "step.blocked"; stepIndex: number; reason: string }
  | { type: "step.failed"; stepIndex: number; evidence: string }
  | { type: "artifact.upserted"; kind: ArtifactKind }
  | { type: "receipt.updated"; receiptId: string }
  | { type: "approval.needed"; approvalId: string }
  | { type: "mission.waiting_on_you" }
  | { type: "mission.done" }
  | { type: "mission.failed" }

Public Acme stays id: acme-0491, receipt #0491.  
Failed seed stays failed-0502.  
Live missions get new ids. Do not overwrite acme-0491 with user runs.

Gate 3 — Policy

Two classes of work.

Auto (no approval)

read calendar
search mail
read drive
web research
summarize
draft brief / agenda / follow-up
propose a prep block (do not write it yet if policy is all_writes)

Gated (Approval + Do it)

send email
write or update a calendar event
share a document externally
post to Slack / anything leaving the user’s name

Settings already has:

all_writes — confirm external sends and calendar writes
external_sends — confirm sends only; calendar write may auto-run

The engine reads that policy from the user.  
The model does not choose the policy.

unauthorized on a receipt is always 0 if the engine is correct.  
If a gated tool runs without an approved row, fail the mission.

Gate 4 — Run loop

One loop. No swarm.

intent
  → normalize
  → plan (≤ 8 steps)
  → for each step
        if gated and not approved: block, write approval, waiting_on_you, stop
        else run tool
        write evidence
        upsert artifact if any
        emit event
  → write receipt
  → status done | waiting_on_you | failed

Planning rules:

Max 8 steps
Step labels are user-facing English, like the Acme list
Evidence is one short clause
The model may propose tools. The allowlist decides.
If planning fails, create a 1-step failed mission and still write a receipt

Time budget:

Live run target < 45s to waiting_on_you or done
UI ticks may batch events; do not stream tokens into PlanList

Gate 5 — HTTP API

Base: existing FastAPI. Session from desk_session.

POST   /missions
       body: { intent: string }
       auth required
       creates draft, queues run, returns mission

GET    /missions
       auth required
       user’s missions only

GET    /missions/:id
       acme-0491 and failed-0502 public
       others auth + owner

POST   /missions/:id/replay
       public for acme-0491 only
       replays seed events, does not call live tools

GET    /missions/:id/events
       SSE
       auth except public demo ids

GET    /missions/:id/receipt
GET    /missions/:id/artifacts
GET    /approvals
POST   /approvals/:id/do
POST   /approvals/:id/draft

POST /missions is what CommandBar calls once wired.  
Until wired, CommandBar may keep creating local Draft cards.  
Do not wire CommandBar in Agent Gate 1.

POST /approvals/:id/do

verify session user owns the row
verify status is needed
run the one gated tool
mark approval approved
mark step done
set artifact sent if mail
receipt NEEDS YOU becomes empty
status done if no other blocks
emit events

POST /approvals/:id/draft

leave mission waiting_on_you
do not call the gated tool

Gate 6 — Tool allowlist

Implement adapters behind this interface:

type ToolResult = {
  ok: boolean
  evidence: string
  artifact?: { kind: ArtifactKind; title: string; body: string }
  gated?: boolean
}

| Tool | Auto | Notes |
|---|---|---|
| calendar.read | yes | find event by title/time |
| gmail.search | yes | query, return snippets |
| drive.read | yes | titles + excerpts |
| web.search | yes | company / person research |
| doc.draft | yes | brief, agenda, follow-up |
| calendar.write | gated unless policy external_sends | prep block |
| gmail.send | gated always | never from planner |
| drive.share | gated always | |

v1 live target: web.search + doc.draft real.  
Gmail / Calendar / Drive may be mocked adapters that return Acme-shaped evidence, as long as the policy gate is real.

A mock adapter must still:

emit evidence
refuse gated calls without approval
never set unauthorized by “pretending send succeeded” inside the planner

Gate 7 — Events for the run view

GET /missions/:id/events is SSE.

The existing Mission run view should consume this later.  
For Agent build steps 1–3, a test client may read events. Do not restyle PlanList.

Event order for a healthy Acme-like live run:

mission.started
step.running 1
step.done 1
...
step.blocked 8
artifact.upserted agenda
approval.needed
receipt.updated
mission.waiting_on_you

After Do it:

step.done 8
receipt.updated
mission.done

No assistant.delta events in v1.

Gate 8 — Persistence

Tables / collections:

users already exist
missions
steps
artifacts
receipts
approvals
run_events optional; SSE may replay from steps + artifacts

Rules:

every personal row has userId
never return another user’s approval
public seed rows have userId = null and fixed ids
signed-in clone of seed is a new mission id, not acme-0491

SQLite is enough for the hackathon. Postgres later.

Gate 9 — Model use

One planner call per mission. Optional one writer call per artifact.

Planner output must be structured JSON:

{
  "steps": [
    { "label": "Calendar inspected", "tool": "calendar.read" }
  ]
}

Reject plans with unknown tools.  
Reject plans with a gated tool before the last step unless the intent is only that action.

Writer turns tool evidence into brief / agenda body.  
Writer never claims “sent.”

If no API key, use a deterministic planner for known intents:

contains “Acme” and “meeting” → official 8-step Acme plan
else → 4-step generic: understand intent, research, draft, request approval

Gate 10 — Failure

A failed step still writes a receipt.

Receipt for failed-0502 shape:

DONE: steps that finished
NEEDS YOU: empty or Retry
failed step listed in DONE? No. List under a FAILED line if you add one field  
  Keep UI compatibility: failed step state failed, receipt still printable

Retry step may call POST /missions/:id/retry?step= later.  
v1 may no-op on the public failed seed.

Gate 11 — Security

Session on every personal route
CSRF: same-site cookie + same origin
Gated tools need approval id, not just mission id
Cap tool payload sizes
Cap plan to 8 steps
Cap one live run per user at a time
Do not put OAuth provider tokens in receipts
Evidence may include titles and counts, not full email bodies in the receipt header

Gate 12 — What the UI may call later

Keep these mappings stable.

| UI | API |
|---|---|
| CommandBar Enter | POST /missions |
| Missions board | GET /missions |
| Run view open | GET /missions/:id + SSE |
| Replay on Acme | POST /missions/acme-0491/replay |
| Do it | POST /approvals/:id/do |
| Keep as draft | POST /approvals/:id/draft |
| Receipts list | receipts from user’s missions + public seeds if linked |

Do not implement the UI wiring in Agent Gates 1–4.

Gate 13 — Acceptance

[ ] POST /missions with a session creates a mission and receipt
[ ] Planner cannot call gmail.send
[ ] Gated tool without approval leaves waiting_on_you
[ ] POST /approvals/:id/do is the only send path
[ ] Receipt always exists, including failure
[ ] unauthorized is 0
[ ] acme-0491 still public and seed-based
[ ] User A cannot Do it on User B’s approval
[ ] No new desk nav
[ ] No UI restyle

Gate 14 — Build order for Grok CLI

Work one step. Stop after each. Score Gate 13. Do not open the next step until told.

Step 1 — Store + Acme seed in the database
Persist missions/steps/artifacts/receipts/approvals.  
Load acme-0491 and failed-0502 as public rows.  
GET /missions/acme-0491 returns the current UI contract JSON.  
No model. No tools.

Step 2 — Runner with mocked tools
In-process runner executes a plan against mock adapters.  
Acme-shaped intent produces the 8-step plan and blocks on send.  
Writes events to memory or table.  
POST /missions auth required.

Step 3 — SSE
GET /missions/:id/events streams the run.  
A curl/test page may consume it. Do not change MissionRun.tsx unless a 5-line hook is required and you are told to.

Step 4 — Approvals API
GET /approvals  
POST /approvals/:id/do  
POST /approvals/:id/draft  
Mock send records sentAt on the artifact and does not call Gmail until a later gate.

Step 5 — One live tool
web.search or doc.draft with a real key if present, else mock.  
Deterministic planner still used when no model key.

Step 6 — Score Gate 13
Fix misses only. Do not restyle UI. Do not wire CommandBar unless all checks pass and you are asked.

Gate 15 — If unsure

Prefer a mocked tool + a true gate  
over a live send + a sloppy gate.

Prefer one planner  
over four agents.

Prefer a short evidence line  
over a transcript.

Prefer leaving Acme public and fake  
over breaking the judge script.

The engine is correct when the receipt is true and nothing left the user’s name before Do it.
