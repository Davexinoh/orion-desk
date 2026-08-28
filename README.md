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
