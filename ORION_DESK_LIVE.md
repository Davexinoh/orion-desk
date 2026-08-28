

Orion Desk — Live Tools Spec

Version: 1.0  
Owns: turning every mock adapter into a real provider call  
Does not own: UI look, auth providers list, public Acme seed  
Authority:  
UI master wins on chrome.  
AUTH wins on session.  
AGENT wins on policy.  
This file wins on adapters and env.

If a live tool can send mail or write calendar without POST /approvals/:id/do, the build is wrong.

Gate 0 — Target state

| Tool | Live provider | When |
|---|---|---|
| web.search | Tavily | TAVILY_API_KEY |
| doc.draft | OpenAI or Anthropic | OPENAI_API_KEY or ANTHROPIC_API_KEY |
| calendar.read | Google Calendar | Google OAuth |
| calendar.write | Google Calendar | Google OAuth + approval or policy |
| gmail.search | Gmail API | Google OAuth |
| gmail.send | Gmail API | Google OAuth + Do it only |
| drive.read | Drive API | Google OAuth |
| drive.share | Drive API | Google OAuth + Do it only |

No key → that tool stays mock and reports mode: mock.  
Never crash the runner because a key is missing.  
Never pretend a mock send is live.

Gate 1 — Hard bans

Planner calling gmail.send, calendar.write, or drive.share
Storing Google refresh tokens in git or receipts
Dumping raw search hits or full email bodies onto the receipt header
Blocking /desk/m/acme-0491 on Google
Requiring Tavily for the public demo
Changing ActionReceipt field names
New desk nav items
UI restyle

Gate 2 — Env

Search
TAVILY_API_KEY=

Drafting
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LLM_PROVIDER=openai

Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI={APP_ORIGIN}/auth/google/callback

Already exist
TELEGRAM_BOT_TOKEN=
SESSION_SECRET=
APP_ORIGIN=
MAIL_FROM=
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASS=

Redirect URI must match Google Cloud exactly.  
Commit .env.example with empty values. Never commit .env.

Gate 3 — Google OAuth

Settings rows become real.

Gmail      Connect | Connected
Calendar   Connect | Connected
Drive      Connect | Connected

One Google grant can cover all three. Still show three rows.

Scopes (start here, do not ask for more):

openid
email
profile
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/calendar.readonly
https://www.googleapis.com/auth/calendar.events
https://www.googleapis.com/auth/drive.readonly
https://www.googleapis.com/auth/drive.file

drive.file = files Desk creates. Do not request full Drive control in v1.

Flow:

Settings → Connect → GET /auth/google/start
Google consent
GET /auth/google/callback
Store { access_token, refresh_token, expiry, scopes } keyed by userId
Refresh on 401
Disconnect deletes tokens, does not delete the Desk user

Missing grant: tool returns  
ok: false, evidence: "Gmail is not connected."  
Step fails or skips per runner rules. Receipt still writes.

Gate 4 — Adapter contract

Keep the existing interface.

type ToolResult = {
  ok: boolean
  evidence: string          // one clause
  artifact?: { kind: "brief" | "agenda" | "calendar" | "followUp"; title: string; body: string }
  gated?: boolean
  mode: "live" | "mock"
}

Evidence examples:

Found event: Acme / Tomorrow 14:00
Read 6 emails
No calendar event matched
Gmail is not connected.
Tavily: 3 sources on Acme

Receipt header tools list stays short names: Calendar · Gmail · Drive · Web

Gate 5 — Tool behavior

web.search
Live: Tavily query from the step.  
Evidence: Tavily: {n} sources on {topic} plus first title if needed.  
Cap 3 titles. No raw dump.

doc.draft
Live: LLM writes brief / agenda / follow-up from prior step evidence only.  
Must not invent “sent.”  
If no LLM key: deterministic template from evidence.

calendar.read
Find event by title + window in the user’s primary calendar.  
If none: ok: true is allowed with evidence No event matched; using stated time.  
Do not fail the whole mission only because the event title differs.

gmail.search
Search recent mail for the other party / subject.  
Evidence: Read {n} emails  
Do not paste bodies into the receipt. Bodies may go to the planner context, truncated.

drive.read
Search files by name / query.  
Evidence: {n} documents reviewed  
Excerpts to planner only.

calendar.write  (gated)
Creates the prep block.  
Runner never calls this.  
POST /approvals/:id/do may call it when policy is all_writes or when that row’s risk is Calendar write.

gmail.send  (gated always)
Sends the agenda / follow-up to attendees.  
Only from Do it.  
On success: artifact.sent = true, evidence Agenda sent to {n} attendees.

drive.share  (gated always)
Only from Do it. v1 may defer if time is short; keep mock + gate rather than a sloppy live share.

Gate 6 — Policy unchanged

Auto: read + search + draft + web  
Gated: send + share + calendar write when policy is all_writes

Settings radios already exist. Engine must read them.

unauthorized stays 0.  
If a gated live call happens without an approved row, fail the process and do not send.

Gate 7 — Public vs live

| Id | Behavior |
|---|---|
| acme-0491 | Seed only. No Google. No Tavily. |
| failed-0502 | Seed only. |
| m-* live missions | Real adapters when keys/grants exist |

Signed-in CommandBar already creates m-*.  
Do not overwrite public seed.

Gate 8 — HTTP extras

GET  /auth/google/start
GET  /auth/google/callback
POST /auth/google/disconnect
GET  /integrations
     { gmail, calendar, drive, tavily, llm } each { connected or keyPresent, mode }

/integrations feeds Settings.  
Do not put tokens in that payload.

Gate 9 — Build order

One step. Stop. Do not restyle.

Step 1 — Integration status + Settings
GET /integrations  
Settings shows Connect / Connected / Coming soon from server.  
Google buttons may 501 until step 2.  
Tavily/LLM show key present/absent only.

Step 2 — Google OAuth start/callback/token store
Connect Calendar/Gmail/Drive works.  
No tool calls yet.

Step 3 — Live reads
calendar.read gmail.search drive.read use tokens when connected, else mock with mode: mock.

Step 4 — Live web.search + doc.draft
Tavily + LLM when keys exist, else mock.

Step 5 — Live gated writes
gmail.send and calendar.write only inside POST /approvals/:id/do.  
Drive.share may stay mock.

Step 6 — Score
Planner still cannot send
Public Acme still seed
Do it is the only live send
Missing key → mock, mission still completes or waits
No UI restyle

Gate 10 — Acceptance

[ ] Missing keys do not crash POST /missions
[ ] Acme public Replay unchanged
[ ] Connected Gmail search reads the user’s mailbox
[ ] Connected Calendar read uses the user’s calendar
[ ] Agenda is not emailed until Do it
[ ] Do it with Gmail connected sends one message
[ ] Do it without Gmail returns a failed step + receipt, sent false
[ ] Tokens never appear in receipts or SSE
[ ] User A cannot use User B’s Google grant
[ ] Settings rows match /integrations

Gate 11 — If unsure

Ship a live read before a live send.  
Ship a refused send before a guessed send.  
Keep mock as fallback, labeled in /integrations, not as a silent lie.

