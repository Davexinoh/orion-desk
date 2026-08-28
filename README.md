# Orion Desk

Intent to action. Desk plans, acts, and stops before anything leaves your name.

## Public paths

- `/` is public
- `/desk/m/acme-0491` is the public demo (Replay, no account)

Sign in is Telegram + email. `/desk` and other desk routes need a session.

## Run locally

Copy env, then start web and server.

```bash
copy .env.example .env
```

Web (http://127.0.0.1:5173):

```bash
cd web
npm install
npm run dev
```

Server (http://127.0.0.1:8787):

```bash
cd server
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

Vite must proxy:

- `/auth`
- `/missions`
- `/approvals`
- `/integrations`

With no keys, the Acme demo still runs. Do not commit `.env` or `server/data`.

## Railway one-service

One service: build the web app, then uvicorn serves `web/dist` at `/` and the API at `/auth` `/missions` `/approvals` `/integrations`.

Build:

```bash
npm ci --prefix web && npm run build --prefix web
```

Start:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir server
```

`nixpacks.toml` / `railway.toml` run those. Production refuses to boot without `SESSION_SECRET`. Cookie `Secure` is on when `APP_ORIGIN` is `https://`. CORS allows `APP_ORIGIN`. `/` and `/desk/m/acme-0491` stay public.

Env (names only):

```
APP_ORIGIN
SESSION_SECRET
TELEGRAM_BOT_TOKEN
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI
TAVILY_API_KEY
OPENAI_API_KEY
```

## Telegram Login (live APP_ORIGIN)

`GET /auth/config` returns `{ telegramBot }` when `TELEGRAM_BOT_TOKEN` is set (uses `TELEGRAM_BOT_USERNAME` if set, else Telegram `getMe`). The sign-in widget uses that username. `POST /auth/telegram` verifies the widget hash with the bot token and sets `desk_session`.

Operator sequence:

1. @BotFather → `/newbot` → save token and `@username`
2. `TELEGRAM_BOT_TOKEN` in Railway variables
3. `TELEGRAM_BOT_USERNAME` if the app reads it separately
4. `APP_ORIGIN=https://<railway-host>` with no trailing slash
5. BotFather → domain for Login Widget = `<railway-host>` only  
   example: `orion-desk-production.up.railway.app`  
   not `https://`, not a path
6. Redeploy
7. Open `APP_ORIGIN/sign-in` → Continue with Telegram mints `desk_session`
8. `/` and `/desk/m/acme-0491` still work signed out

Do not commit the token.
