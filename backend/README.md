# GitHub Repo Bot — Backend

FastAPI backend for a bot that reacts to GitHub repo activity: OAuth login,
webhook ingestion, configurable rules, GitHub write-back (label/comment), and
Slack notifications.

## Stack
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg, pointed at Supabase Postgres
- httpx for GitHub/Slack API calls, `tenacity` for retrying transient failures
- Sessions: signed JWT in an httponly cookie (not Supabase Auth — we need the
  user's GitHub access token for API calls, so a single custom session keeps
  one source of truth)
- GitHub access tokens are encrypted at rest with Fernet before being stored

## Project layout
```
app/
  main.py            FastAPI app, middleware, router registration
  config.py          Settings loaded from env
  database.py        Async engine/session, table creation on startup
  models.py          SQLAlchemy models: User, Repo, Event, Rule, ActionLog
  schemas.py         Pydantic request/response models
  security.py        Webhook signature verification, JWT sessions, encryption
  dependencies.py    get_current_user auth dependency
  routers/
    auth.py          GitHub OAuth login/callback/logout
    repos.py         List/connect/disconnect repos (creates the GitHub webhook)
    webhooks.py       POST /webhooks/github — signature check, dedupe, ack, enqueue
    rules.py         CRUD for user-configured rules
    events.py        Dashboard event log + manual retry
  services/
    github_client.py  GitHub REST API calls
    slack_client.py   Slack Incoming Webhook call
    rule_engine.py     Matches an event against a user's configured rules
    event_processor.py Orchestrates rule matching + actions + logging
db/schema.sql        Reference SQL schema (tables are also auto-created on boot)
```

## How it satisfies the reliability/security bar
- **Forged/replayed requests**: `/webhooks/github` verifies the
  `X-Hub-Signature-256` HMAC against `GITHUB_WEBHOOK_SECRET` using a
  constant-time comparison; anything that doesn't match is rejected with 401
  before it's parsed or stored.
- **Duplicate delivery**: GitHub's `X-GitHub-Delivery` id is stored with a
  unique DB constraint. Redelivered events are detected and short-circuited
  (no re-processing, no duplicate label/comment/Slack message).
- **Downstream failures**: the webhook handler ACKs (200) immediately after
  persisting the raw event, then processes it in a background task — so a
  slow/broken GitHub or Slack call can't cause GitHub to time out and pile up
  retries. Each action (label / comment / Slack) is wrapped individually, so
  one failing action doesn't block the others or lose the event; the event's
  final status (`processed` / `processed_with_errors` / `failed`) and every
  action attempt are recorded, and failed events can be manually re-run via
  `POST /api/events/{id}/retry`.
- **Secrets**: nothing is hardcoded — everything comes from environment
  variables; GitHub access tokens are encrypted before being written to the
  database; `.env` is gitignored.

## Running locally

1. Create a Python venv and install deps:
   ```
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in real values (see below).
3. Run:
   ```
   uvicorn app.main:app --reload
   ```
   Tables are created automatically on startup against your Supabase DB.
4. Since GitHub OAuth and webhooks can't hit `localhost`, use a tunnel
   (e.g. `ngrok http 8000`) and set `BACKEND_PUBLIC_URL` /
   `GITHUB_OAUTH_REDIRECT_URI` to the tunnel URL while testing locally.

## Environment variables
See `.env.example` for the full list and where to get each value:
- `DATABASE_URL` — Supabase connection string (asyncpg driver)
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` — GitHub OAuth App
- `GITHUB_OAUTH_REDIRECT_URI` — must exactly match the OAuth App's callback URL
- `GITHUB_WEBHOOK_SECRET` — used to verify webhook signatures
- `SLACK_WEBHOOK_URL` — Slack Incoming Webhook URL
- `ENCRYPTION_KEY` — Fernet key for encrypting stored GitHub tokens
- `SESSION_SECRET` — signs the session JWT
- `BACKEND_PUBLIC_URL` / `FRONTEND_URL` — used for the webhook URL and CORS/redirects

## Deploying (Render)
1. Push this repo to GitHub.
2. Render → New → Web Service → connect the repo → it will detect the
   `Dockerfile` (or set build command `pip install -r requirements.txt` and
   start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT` if not
   using Docker).
3. Add all the env vars above in the Render dashboard. Set
   `BACKEND_PUBLIC_URL` to the Render-assigned URL and
   `GITHUB_OAUTH_REDIRECT_URI` to `<that-url>/auth/github/callback` — then
   update the callback URL on the GitHub OAuth App to match.
4. Note: Render's free tier spins the service down after 15 minutes idle and
   takes 30–60s to wake up. A webhook arriving during that window may hit a
   cold start; GitHub will retry failed deliveries, and our own idempotency
   check means a retry is always safe to process.

## API quick reference
- `GET /auth/github/login` — start OAuth
- `GET /auth/github/callback` — OAuth callback (redirects to frontend)
- `GET /auth/me` — current user
- `GET /api/repos/available` — repos you can connect
- `POST /api/repos` `{full_name}` — connect a repo (creates the GitHub webhook)
- `DELETE /api/repos/{id}` — disconnect
- `POST /webhooks/github` — GitHub webhook receiver
- `GET /api/rules` / `POST /api/rules` / `PUT /api/rules/{id}` / `DELETE /api/rules/{id}`
- `GET /api/events` — dashboard log
- `POST /api/events/{id}/retry` — reprocess a failed event

## Notes
- If a repo owner has configured zero rules, one built-in fallback applies
  (issue title containing "bug" → label `bug` + Slack alert) so the bot does
  something visible out of the box — see `DEFAULT_FALLBACK_RULE` in
  `rule_engine.py`. Any real configured rule always takes priority over it.
