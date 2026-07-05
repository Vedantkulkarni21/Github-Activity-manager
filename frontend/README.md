# Repo Bot — Frontend

React + Vite dashboard for the GitHub repo bot: sign in with GitHub, connect
repos, configure rules, and watch events flow through as a live pipeline.

## Design
- Dark charcoal UI (not pure black) with signal colors borrowed from
  git/CI status conventions: green = success, red = failed, amber = pending,
  indigo = informational/primary.
- Space Grotesk for headers, Inter for UI text, JetBrains Mono for
  repo names, keywords, and log-style data.
- The event log's signature element is the **pipeline row**: each webhook
  renders as trigger → matched actions, rather than a flat table, so the
  dashboard reads like a live event stream.

## Pages
- `/` — Login (GitHub OAuth entry point)
- `/dashboard` — Live event log with retry for failed events
- `/repos` — Connect/disconnect repositories
- `/rules` — Create and delete keyword-matching automation rules

## Running locally

```
npm install
cp .env.example .env   # point VITE_API_URL at your backend
npm run dev
```

Runs on http://localhost:5173 by default. Your FastAPI backend's
`FRONTEND_URL` env var should match this so CORS and the post-login
redirect work.

## Auth model
The backend issues an httponly session cookie on OAuth login — there's no
token stored in the browser's JS-accessible storage. All API calls use
`credentials: "include"` (see `src/api/client.js`) so the cookie rides along
automatically. `AuthContext` calls `GET /auth/me` on load to determine
whether a session is active.

## Building for production

```
npm run build
```

Outputs static files to `dist/`. Deploy `dist/` to Vercel, Netlify, or
Render's static site hosting. Set `VITE_API_URL` as a build-time environment
variable on whichever host you use, pointing at your deployed backend.

## Notes
- Polling (every 8s) is used for the event log rather than websockets, to
  keep the "everything free, no infra beyond Render + Supabase" constraint
  simple. A websocket/SSE upgrade would be a natural next step for true
  real-time updates.
