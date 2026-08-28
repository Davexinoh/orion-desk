

Orion Desk — Master UI Build Spec

Version: 1.0  
Product: Orion Desk  
Surfaces: Marketing site · Web app · Telegram templates  
Authority: If a later request conflicts with this file, this file wins.

Gate 0 — Read before any code or screen

You are not building a chatbot.  
You are not building a crypto dashboard.  
You are not building a SaaS analytics admin.  
You are not wrapping an LLM in a shadcn sidebar.

You are building a private operations desk for an intent-to-action agent.

Primary objects, in this order:

Mission
Action Receipt
Approval
Memory

Chat is an input method only.  
The UI shows work being executed, work that needs a signature, and work that already happened.

If a screen cannot serve one of the four objects, delete it.

Gate 1 — Hard bans

If you generate any of these, delete and rebuild.

Visual bans

Purple, violet, magenta, electric teal, neon green, cyan glow
Gradients on backgrounds, buttons, cards, or text
Glassmorphism, aurora blobs, mesh gradients, AI sparkles
Robot mascot, planet logo, token charts, wallet-connect hero
Drop shadows larger than 8px / 8% opacity
Radius above 10px on cards, 8px on controls, 999px except tiny status dots
Inter-only typography with no serif contrast
Light mode for v1
Emoji as decoration in the web app
Icon soup (more than 4 icons in a card)

UX bans

“Ask me anything”
“How can I help you today?”
“As an AI…”
Empty state that is only a chat box
Sidebar with more than 5 items
KPI dashboard with charts as home
Settings page with 20 toggles
Tabs named Overview / Analytics / Insights / Dashboard
Onboarding carousel
Confetti, bounce, pulse glow, typing sparkle theater

Component bans

Default shadcn Dashboard template
ChatGPT-style message list as home
Generic user DataTable
Calendar heatmap
Donut charts for “productivity score”

Copy bans

“Unlock your potential”
“The future of work”
“Next-gen AI”
“Web3 productivity”
“Powered by agents”
Exclamation marks in product UI
sleek, cutting-edge, revolutionary, seamless, magical

Gate 2 — Product mental model

User states an outcome in one sentence.  
Orion Desk turns that sentence into a Mission.  
The Mission runs tools.  
Low-risk work happens automatically.  
Consequential work stops behind an Approval.  
Every Mission produces an Action Receipt.

Loop on every surface:

Intent → Context → Plan → Action → Verification

Required demo mission

I have a meeting with Acme tomorrow at 2 PM. I haven't prepared anything. Handle it.

That mission must produce:

Meeting identified
Emails analyzed
Documents reviewed
Company researched
Brief generated
Prep block scheduled
Follow-up drafted
One pending approval:** Send agenda to attendees

Gate 3 — Design references

Steal structure and restraint, not brand colors.

Use

| Source | URL | Steal |
|---|---|---|
| Linear | https://linear.app | Density, tiny labels, dark surfaces, no junk widgets |
| Vercel Dashboard | https://vercel.com/dashboard | Quiet chrome, precise status, log energy |
| Raycast | https://www.raycast.com | Command-first input, result as object |
| Superhuman | https://superhuman.com | Speed, short copy, split inbox for things that need you |
| Mercury | https://mercury.com | Statement seriousness for receipts |
| Stripe | https://stripe.com | Receipt hierarchy, line items, printable calm |
| Things 3 | https://culturedcode.com/things | One obvious next action |
| Notion Calendar | https://www.notion.so/product/calendar | Time as a first-class object |
| Boarding passes / itineraries | — | Receipt geometry |

Do not look like

ChatGPT / Claude chat shells
Notion marketing homepage
Typical purple AI landing pages
Crypto launchpads, including orionagents.org
Tailwind UI / shadcn dashboard-01 blocks

orionagents.org is the parent ecosystem. Do not copy its DeFi launchpad: no TVL, no Gold Tier, no Invest, no Connect Wallet as Desk’s first action.

Gate 4 — Design tokens

Do not improvise a new palette.

:root {
  --bg: #0B0C0A;
  --bg-elev-1: #11130F;
  --bg-elev-2: #161814;
  --bg-elev-3: #1C1F19;
  --line: #2A2C28;
  --line-strong: #3A3D36;
  --text: #E8E4D9;
  --text-muted: #8B877A;
  --text-faint: #5E5B52;
  --accent: #7C8F6C;
  --accent-dim: #2A3326;
  --warn: #C4A15A;
  --warn-dim: #3A3018;
  --danger: #B45A4A;
  --good: #7C8F6C;

  --pending: var(--warn);
  --running: #A3B18A;
  --done: var(--accent);
  --idle: var(--text-faint);
  --blocked: var(--danger);

  --font-sans: "Geist", "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-serif: "Newsreader", "IBM Plex Serif", "Iowan Old Style", Georgia, serif;
  --font-mono: "Geist Mono", "IBM Plex Mono", ui-monospace, monospace;

  --r-sm: 4px;
  --r-md: 6px;
  --r-lg: 8px;
}

Type sizes: 11 / 12 / 13 / 14 / 16 / 20 / 28 / 40  
Line height: 1.25 titles · 1.45 body · 1.55 receipts  
Weights: 400, 500, 600 only  
Spacing: 4 / 8 / 12 / 16 / 24 / 32 / 48  
Card padding: 16px  
Receipt padding: 20–24px  
Border: 1px solid var(--line)  
Shadow: almost none; if needed 0 8px 24px rgba(0,0,0,0.35)

Gate 5 — Logo and wordmark

Mark:** 16–20px monoline 4-point compass / desk-pin, color --text
Wordmark:** Orion sans 500 + Desk serif 400
No slogan in app chrome
Marketing hero may use: Your intent becomes action.
Never: AI-powered productivity suite.
Favicon: compass on --bg

Gate 6 — Information architecture

Web app nav — max 5

Missions
Approvals
Receipts
Memory
Settings

Default landing after login: Missions

Settings only contains

Profile
Connected tools
Telegram link status
Approval policy
Danger zone

Marketing nav — max 5

Product
Receipts
Demo
GitHub
Open app / Open Telegram

Gate 7 — Web app screens

Build these and no others for v1.

7.1 Missions (home)

Layout

Left rail 220px, collapse to 64px below 1100px
Main canvas
Right drawer 380px when a mission is selected

Command bar

Serif placeholder: What should get done?
Submit on Enter
Helper, 12px muted: State an outcome. Desk will plan and act.

Filters: Active · Waiting on you · Done  
Default: Active + Waiting on you

Mission card

A work object, not a chat bubble.

Intent sentence in serif, 16–18px, 2-line clamp
Status pill: Running / Waiting on you / Done / Draft / Idle
Step meter: 6 of 8 steps + 2px progress rule
Tools as text: Calendar · Gmail · Drive · Web
Meta: Started 9:12 · 42s · ~47 min saved
If pending: 2px amber left hairline + 1 action needs you

Grid: 2 columns desktop, 1 mobile  
Card surface: --bg-elev-1 + 1px line  
Click → receipt drawer + live plan

Required seed cards

| Card | Status | Detail |
|---|---|---|
| Prepare Acme meeting | Running | 6/8 · waiting approval |
| Research Q2 benchmarks | Done | Saved 1h 12m |
| Draft investor update | Draft | 2/6 |
| Sync pricing feedback | Idle | Waiting for input |

Empty state: no illustration. Show the Acme sentence as a clickable example that fills the command bar.

7.2 Mission run view

Left 58%: live plan checklist
Right 42%: artifacts Brief · Agenda · Calendar · Follow-up
Documents use serif body on dark paper
ApprovalBar only if pending_consequential_actions > 0

ApprovalBar

Left: Send agenda to 4 attendees
Right: Keep as draft (ghost) · Do it (accent)
No third button

Live ticks, one line each:

Found the 2pm event.
Read 6 emails.
Drafted agenda. Not sent.

7.3 Action Receipt

Signature artifact. Must look printable.

ORION DESK
RECEIPT  #0491

INTENT
I have a meeting with Acme tomorrow at 2 PM. I haven't prepared anything. Handle it.

DONE
✓ Calendar inspected
✓ 6 emails read
✓ 2 documents reviewed
✓ Company researched
✓ Brief generated
✓ Prep block placed on calendar

NEEDS YOU
→ Send agenda to 4 attendees

TOOLS
Calendar · Gmail · Drive · Web

TOTALS
Elapsed                 42 seconds
Not spent               ~47 minutes
Unauthorized actions    0

Desk does not send external messages without approval.

Receipt appears in:

Drawer
/receipts/:id
Print / PDF stylesheet

Receipts index is a list, not cards:

id · intent · status · elapsed · saved · date

7.4 Approvals

Split inbox.

Left: pending consequences only
Right: exact artifact preview

Each row:

Verb + object: Send agenda to Jane, Mark, Priya, Dan
Parent mission intent
Age: 3m ago
Risk: External send / Calendar write / File share

Actions: Do it / Keep as draft / Edit first  
Zero state: Nothing needs your signature.

7.5 Memory

Three sections only.

User memory  
Keep emails concise · No meetings before 10:00 · Agendas in bullets

Project memory  
Groups: Acme · Q2 planning · Investors

Execution memory  
Agenda created yesterday · user kept as draft

No embeddings language. No vector visualizations.

7.6 Settings

Rows:

| Tool | State |
|---|---|
| Gmail | Connected / Connect |
| Calendar | Connected / Connect |
| Drive | Connected / Connect |
| Notion | Coming soon |
| Telegram | Linked as @user |

Approval policy

Confirm all external sends and calendar writes (default)
Confirm external sends only
Never offer “autonomous send everything”

Gate 8 — Marketing website

One long dark editorial page. Not a crypto landing page.

Hero — Your intent becomes action. Subhead max 18 words. CTA: Open Telegram / Watch the Acme demo. Visual: Receipt, not a robot.
Problem — Getting work done is coordination, not tasks.
Loop — Intent → Context → Plan → Action → Verification
Receipt — real component in situ
Demo — 20–30s walkthrough ending on 8 actions · 5 integrations · 43 seconds · ~47 minutes not spent · 0 unauthorized actions
Surfaces — Telegram for talking. Web for seeing.
Safety — Automate the work. Confirm the consequences.
Footer — GitHub · X · Telegram · orionagents.org · Built for the Orion Agents Builder Hackathon. No token price. No wallet modal.

Stack: Next.js + Tailwind · Geist + Newsreader via next/font · motion only on hero fade, 200ms.

Gate 9 — Telegram templates

Allowed message types:

User intent
MissionCard
TickLine (max 8, one clause each)
ReceiptBlock
ApprovalKeyboard
ArtifactPreview

ORION DESK
Mission · Running
Prepare me for the Acme meeting.
6/8 steps
Calendar · Gmail · Drive · Web

Keyboard:

Do it
Keep as draft
Open receipt

/start

Orion Desk
State an outcome.
Example: I have a meeting with Acme tomorrow at 2. Handle it.

Banned: welcome essays, stickers, 600-word first replies, more than one question before work starts.

Gate 10 — Motion

120–180ms
cubic-bezier(0.2, 0.8, 0.2, 1)
Progress fills left → right
Checks stagger 90–120ms
Drawer 200ms
No bounce, no sound, honor prefers-reduced-motion

Gate 11 — Copy deck

Voice: chief of staff. Dry. Specific. No cheer.

| Use | Never |
|---|---|
| Found the 2pm event. | Awesome, I took care of that! |
| Drafted agenda. Not sent. | Let’s start your productivity journey. |
| 1 action needs you. | As an AI… |
| Nothing needs your signature. | |
| Goal completed. | |

Placeholder: What should get done?
Approve: Do it
Reject: Keep as draft
Time saved: Not spent
Never: AI score, magic minutes

Gate 12 — Component inventory

AppShell  
CommandBar  
NavRail  
StatusPill  
MissionCard  
MissionGrid  
PlanList  
ArtifactPane  
ApprovalBar  
ApprovalRow  
ActionReceipt  
ReceiptList  
MemoryFact  
MemoryGroup  
ToolRow  
EmptyExample  
MarketingReceipt  
DemoStats

Do not add ChartCard, StatWidget, TeamAvatarStack, or a notification center beyond an Approvals badge.

Gate 13 — Measurements

| Element | Size |
|---|---|
| Header | 56px |
| Nav rail | 220px |
| Command bar | 48px |
| Mission card min height | 148px |
| Receipt drawer | 380–420px |
| Marketing max width | 1080px |
| App canvas max | 1280px |
| Mobile breakpoint | 768px |

Mobile: bottom bar with Missions, Approvals, Receipts, Memory. Receipt becomes a full-screen sheet.

Gate 14 — Required states

Mission: draft, queued, running, waiting_on_you, done, failed, idle  
Step: pending, running, done, skipped, blocked  
Approval: needed, approved, dismissed, edited  
Integration: connected, disconnected, coming_soon, error  
Receipt: complete, partial, failed

Failed missions still render a receipt. CTA: Retry step / Open log. Never only Something went wrong.

Gate 15 — Accessibility

Body contrast ≥ 7:1
Focus: 1px --accent, 2px offset
Keys: Enter sends · j/k move missions · Enter opens receipt · a approvals · Esc closes drawer
Status exists in text, not color alone

Gate 16 — Hackathon demo path

The UI must support this exact path:

Marketing site loads. Receipt visible in 1 second. No wallet modal.
Watch demo or Open app.
Command bar accepts the Acme sentence.
Mission card appears as Running.
Plan ticks complete in under 8 seconds of UI time.
ApprovalBar appears.
User clicks Do it.
Receipt updates. Unauthorized actions = 0.
Stats: 8 actions · 5 integrations · 43 seconds · ~47 minutes not spent · 0 unauthorized actions

If this path cannot run, the UI is incomplete.

Gate 17 — Implementation guardrails

Preferred: Next.js App Router + Tailwind + CSS variables from Gate 4.

/app/page.tsx
/app/missions/page.tsx
/app/approvals/page.tsx
/app/receipts/page.tsx
/app/receipts/[id]/page.tsx
/app/memory/page.tsx
/app/settings/page.tsx
/components/...
/lib/demo-data.ts
/lib/tokens.css

Seed demo-data.ts so the UI is complete before backend exists. Mark live vs mocked integrations in Settings.

Gate 18 — Acceptance checklist

[ ] Home is a Mission Board, not a chat transcript
[ ] No purple, no gradient
[ ] Serif used for intents and receipts
[ ] Action Receipt looks like a document
[ ] Approvals is its own surface
[ ] Nav has ≤ 5 items
[ ] Acme demo path works with seed data
[ ] Pending approval is the most important state
[ ] Time saved is labeled Not spent
[ ] Marketing page does not ask to connect a wallet
[ ] Telegram vocabulary matches web
[ ] Failed states still produce a receipt
[ ] Mobile has a 4-item bottom bar
[ ] No robot illustration
[ ] No charts on home

Gate 19 — Build order

tokens.css + fonts  
ActionReceipt  
MissionCard + MissionGrid  
AppShell + CommandBar  
ApprovalBar + Approvals page  
Seed Acme demo data  
Mission run view  
Memory + Settings  
Marketing page using the real Receipt  
Telegram preview page  
Responsive + keyboard + reduced motion  
Run Gate 18 and fix misses  

Work one step at a time. After each step: score against Gate 18, list misses, fix before continuing.

Gate 20 — If unsure

Choose the calmer option.  
Choose less color.  
Choose fewer elements.  
Choose a document over a widget.  
Choose Do it over Confirm and send now.

The product should feel like a person who already did the work, put the folder on your desk, and is waiting for a signature.

