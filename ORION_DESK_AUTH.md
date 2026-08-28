

Orion Desk — Auth Spec

Version: 1.0  
Product: Orion Desk  
Surfaces: / public · /sign-in · /desk/* gated · Telegram bot identity  
Authority: ORION_DESK_UI_MASTER.md still owns look and copy. This file owns identity only.  
If a request conflicts with the UI master on color, type, nav, or receipts, the UI master wins.  
If a request conflicts with this file on session, gates, or providers, this file wins.

Gate 0 — Read before any auth code

Desk is a private office. Auth is a door.

You are not building:

a crypto wallet login
a password product
Sign up vs Log in
SSO / SAML
team invites
2FA theater
an onboarding carousel

You are building:

Telegram as the primary identity
Email magic link as the fallback
A session cookie
Sign out
Public demo that stays public

Judge path stays unlocked.  
/ and /desk/m/acme-0491 Replay must work without an account.

Gate 1 — Hard bans

Connect Wallet on /, /sign-in, or /desk
Password fields
“Create account” vs “Log in”
OAuth popup soup (Google, GitHub, Apple) for v1
Blocking the Acme demo behind auth
Wiping seed demo data on sign-out
Putting Sign in as a modal over the hero receipt
Purple, glow, gradient, robot on /sign-in
New top-nav items in the desk app
Auth provider logos larger than 16px

Gate 2 — Who may enter where

| Route | Auth |
|---|---|
| / | Public |
| /sign-in | Public. If already signed in, redirect to /desk |
| /desk/m/acme-0491 | Public demo. Read-only Replay + local Do it |
| /desk/telegram | Public preview |
| /desk Missions board (personal) | Session required |
| /desk/approvals | Session required |
| /desk/receipts | Session required except linked public receipt pages if you add them later |
| /desk/memory | Session required |
| /desk/settings | Session required |

Landing CTAs:

Watch the Acme demo → /desk/m/acme-0491 · public
Open Telegram → Telegram bot / Telegram Login · identity
Header Sign in → /sign-in
After session: header Sign in becomes the display name. Click → Settings

Gate 3 — Identity model

One user. Two possible keys. Same desk.

type User = {
  id: string              // internal uuid
  displayName: string     // editable in Settings
  email: string | null
  telegramId: string | null
  telegramUsername: string | null
  approvalPolicy: "all_writes" | "external_sends"
  createdAt: string
}

Rules:

A user may have email only, Telegram only, or both.
First successful provider creates the user.
Linking the second provider merges into the existing session user.
Never create a second user when linking.
displayName default:
  Telegram: @username or first name
  Email: part before @
Telegram id is the source of truth for the bot.
Email is web-only until Telegram is linked.

Gate 4 — Session

Cookie name: desk_session
httpOnly
Secure in production
SameSite=Lax
Server-side session store or signed token with server verify
TTL: 30 days
Rotate on sign-in
Destroy on sign-out

Do not store the session in localStorage.  
Demo UI state may stay in memory / local seed.  
Personal missions persist server-side only after auth exists. Until the backend is ready, keep seed local and stamp it with userId when session appears.

Unauthorized /desk/* (except public demo routes):  
302 → /sign-in?next=

After sign-in:  
go to next if it starts with /desk, else /desk.

Gate 5 — Sign-in screen

Route: /sign-in  
Same tokens as the desk. No gold.css.

Layout: one column, max width 420px, centered, dark.

Orion Desk

This desk is yours.

Continue with Telegram
Email a link

Watch the Acme demo

Copy rules:

Headline serif: This desk is yours.
No subhead longer than 12 words. Optional: Telegram first. Email if you need it.
Primary button: Continue with Telegram
Secondary: Email a link
Text link: Watch the Acme demo
No “Need an account?”
No legal novel. One line footer: Desk does not send external messages without approval.

Email step 2, same page, no route change:

Email a link

[ email input ]

Send link
Use Telegram instead

After send:

Link sent to {email}
Open it on this device.
Resend in 60s

Errors, dry:

Telegram login failed.
That link expired.
Enter a valid email.
Could not send the link.

Success: no toast parade. Just enter /desk.

Gate 6 — Telegram login

Use the official Telegram Login Widget on /sign-in.  
Widget request access: identity only. No message-write permission from the widget.

Server verify on POST /auth/telegram:

Receive widget payload (id, first_name, username, hash, auth_date, …)
Verify hash with the bot token as specified by Telegram
Reject if auth_date older than 5 minutes
Upsert user by telegramId
If session already has a user without telegramId, link it
Set desk_session
Redirect to next or /desk

Bot and web must use the same bot token family.  
Settings row becomes real:

Telegram    Linked as @user  
or  
Telegram    Link Telegram

Link from Settings reuses the same widget. No second product.

Gate 7 — Email magic link

POST /auth/email/start { email }

Normalize email lowercase
Rate limit: 1 send / 60s / email, 5 / hour / ip
Create a one-time token, TTL 15 minutes, single use
Store token hash, not the raw token
Send a short email

Email body, plain:

Orion Desk

Open this desk:
{ORIGIN}/auth/email/callback?token={token}

This link expires in 15 minutes.
If you did not ask for it, ignore this.

GET /auth/email/callback?token=

Validate token
Mark used
Upsert user by email
If session exists without email, link it
Set cookie
Redirect to next or /desk

No “welcome series.” No marketing mail.

Gate 8 — Sign out

Places:

Settings → Sign out
Header menu on display name → Sign out

POST /auth/logout

Destroy session
Redirect to /
Do not clear the public Acme seed
Do not say “Sorry to see you go”

Gate 9 — Settings rows (auth-aware)

Replace placeholder identity rows only. Do not redesign Settings.

Profile
Display name     [ input ]

Telegram         Linked as @jane   |   Link Telegram
Email            jane@domain       |   Add email

Session
Sign out

Approval policy rows stay as they are.

Danger zone Clear local demo state stays local demo only.  
It must not delete the server user.

Gate 10 — Data ownership after login

Until a real store exists:

Signed-out demo uses global seed
Signed-in user clones seed once into userId-scoped local state
Do it / Memory edits stay on that clone
Sign out returns the next visitor to clean public seed

When a store exists:

missions, approvals, receipts, memory keyed by userId
Acme seed is a template, not one shared mission across all users

Never show User A’s approvals to User B.

Gate 11 — Telegram bot identity

When the bot is live:

/start may include start payload from the Login Widget
If the chat is already linked, do not re-ask identity
Bot copy still Gate 9 of the UI master
The bot does not become a second account system

If web session and bot chat disagree, Settings → Telegram is the repair surface.

Gate 12 — Implementation guardrails

Preferred:

Same Next/Vite app
Auth routes on the existing server
web/src/pages/SignIn.tsx
server/app/auth_telegram.py or equivalent
server/app/auth_email.py
server/app/session.py

Env:

TELEGRAM_BOT_TOKEN=
SESSION_SECRET=
MAIL_FROM=
APP_ORIGIN=

Do not commit tokens.  
Do not log raw magic-link tokens.  
Do not log Telegram hash payloads after verify.

File work order:

Session helper + route gate  
/sign-in UI  
Telegram verify endpoint + widget  
Email start + callback  
Settings link/unlink + Sign out  
Wire landing header Sign in / name  
Keep Acme public  

Gate 13 — Acceptance

[ ] / has no wallet CTA
[ ] / does not require auth
[ ] /desk/m/acme-0491 Replay works signed out
[ ] Other /desk/* routes redirect to /sign-in?next=
[ ] /sign-in has Telegram + email only
[ ] Copy uses Sign in / Sign out / Continue with Telegram / Email a link
[ ] Session is httpOnly cookie
[ ] Logout returns to / and public demo still works
[ ] Settings shows Linked as @user when Telegram is linked
[ ] No new desk nav item
[ ] Gate 4 tokens on /sign-in
[ ] Judge script from the UI freeze still runs cold

Gate 14 — Build order for Grok CLI

Work one step. Stop after each.

/sign-in page only. No backend. Telegram button may be inert. Email step may be local UI.
Session cookie + route gate. Fake session via a dev Sign in as demo hidden behind ?dev=1 if needed.
Telegram verify + real widget.
Email magic link.
Settings + Sign out.
Score Gate 13. Fix misses only. Do not restyle the desk.

Gate 15 — If unsure

Keep the demo public.  
Keep providers to two.  
Keep the door ugly-quiet rather than “on-brand auth.”  
Prefer linking identities over creating duplicates.  
Prefer a magic link over a password.

The user should feel they unlocked their desk, not that they joined a platform.

