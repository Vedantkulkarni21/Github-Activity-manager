# GitHub Activity Manager

A full-stack GitHub automation platform that listens to GitHub repository events, evaluates user-defined rules, performs automated actions, and maintains a live event log.

Built as part of the **Event-Driven GitHub Automation Bot** assignment.

---

## Features

- 🔐 GitHub OAuth authentication
- 📂 Connect multiple GitHub repositories
- 📡 Receive GitHub Webhooks (Issues & Pull Requests)
- ⚙️ Create configurable automation rules
- 💬 Send Slack notifications when rules match
- 📝 Automatically comment on GitHub Issues
- 📊 Dashboard with live event history
- 🔒 Encrypted storage of GitHub access tokens
- 🚀 Fully deployed (Frontend + Backend)

---

## Architecture

```
React (Vite)
        │
        ▼
 FastAPI Backend
        │
 ├── GitHub OAuth
 ├── GitHub REST API
 ├── GitHub Webhooks
 ├── Slack Webhook
 └── PostgreSQL (Supabase)
```

---

## Tech Stack

### Frontend

- React
- Vite
- React Router
- Lucide Icons
- CSS

### Backend

- FastAPI
- SQLAlchemy (Async)
- AsyncPG
- Pydantic
- Cryptography
- JWT Authentication

### Database

- PostgreSQL (Supabase)

### Integrations

- GitHub OAuth
- GitHub REST API
- GitHub Webhooks
- Slack Incoming Webhooks

### Deployment

Frontend: Vercel

Backend: Render (Docker)

Database: Supabase

---

# Project Flow

1. User signs in using GitHub OAuth.
2. GitHub redirects back to the FastAPI backend.
3. Backend exchanges the authorization code for an access token.
4. Access token is encrypted and stored in PostgreSQL.
5. User connects repositories from GitHub.
6. GitHub Webhooks send repository events to the backend.
7. Backend validates webhook signatures.
8. Incoming events are stored in the Event Log.
9. Rules are evaluated.
10. Matching rules perform actions:
    - Send Slack notification
    - Comment on GitHub Issue
11. Dashboard displays all processed events.

---

# Supported Events

- Issues
- Pull Requests

---

# Rule Engine

Rules can be configured from the dashboard.

Example:

```
Event Type:
Issues

Condition:
Title contains "bug"

Actions:
✔ Send Slack Notification
✔ Comment on GitHub Issue
```

---

# Dashboard

Authenticated users can:

- View Event Log
- Connect repositories
- Create Rules
- Delete Rules
- Monitor webhook processing

---

# Security

- GitHub OAuth Authentication
- Signed Session Cookies
- CSRF protection using OAuth state
- GitHub Webhook Signature Validation
- GitHub Access Tokens encrypted before storage
- Secrets managed through environment variables

---

# Local Setup

## Clone Repository

```bash
git clone <repository-url>

cd Github-Activity-manager
```

---

## Backend

```bash
cd backend

python -m venv venv

source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run

```bash
uvicorn app.main:app --reload
```

Backend runs at

```
http://localhost:8000
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at

```
http://localhost:5173
```

---

# Environment Variables

Create a `.env` inside the backend.

```env
DATABASE_URL=

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_OAUTH_REDIRECT_URI=

GITHUB_WEBHOOK_SECRET=

SLACK_WEBHOOK_URL=
SLACK_SIGNING_SECRET=

SESSION_SECRET=
ENCRYPTION_KEY=

BACKEND_PUBLIC_URL=
FRONTEND_URL=
```

Create a `.env` inside the frontend.

```env
VITE_API_URL=http://localhost:8000
```

---

# Deployment

## Frontend

Hosted on **Vercel**

## Backend

Hosted on **Render** using Docker

## Database

Hosted on **Supabase PostgreSQL**

---

# Demo

Frontend

```
<YOUR_VERCEL_URL>
```

Backend

```
<YOUR_RENDER_URL>
```

---

# Repository Structure

```
frontend/
    src/
    public/

backend/
    app/
        routes/
        services/
        models.py
        database.py
        security.py
        main.py

README.md
AI_NOTES.md
.env.example
```

---

# Future Improvements

- AI-powered issue summarization
- Retry mechanism for failed webhook processing
- Event deduplication
- GitHub App authentication
- Multiple notification channels (Discord, Teams)
- Real-time dashboard updates via WebSockets

---

# Author

Vedant Kulkarni