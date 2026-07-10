# AI-First CRM HCP Module

Full-stack assignment implementation for an AI-first Healthcare Professional (HCP) CRM "Log Interaction" screen.

The module lets a life-sciences field representative log HCP interactions in two ways:

- A video-matched `Log HCP Interaction` structured form with HCP search, interaction type, date, time, attendees, topics discussed, voice-note consent, materials/samples, products, and next steps.
- A right-side `AI Assistant` chat panel with an `AI Log` action backed by the LangGraph CRM copilot.

The backend uses FastAPI, SQLAlchemy, LangGraph, and Groq's `gemma2-9b-it` model. SQLite is enabled by default for local review, and the app is Postgres-ready through `DATABASE_URL`.

## Tech Stack

- Frontend: React, Redux Toolkit, Vite, Inter font.
- Backend: Python, FastAPI, SQLAlchemy, Pydantic.
- AI: LangGraph agent plus Groq LLM service.
- Database: SQLite by default, PostgreSQL compatible via environment config.

## LangGraph Agent Tools

The CRM agent exposes six sales workflow tools:

1. `search_hcp`: finds HCP records by name, specialty, organization, or territory.
2. `log_interaction`: logs a new interaction and uses the LLM to extract summary, sentiment, intent, products, objections, and next steps.
3. `edit_interaction`: updates an existing interaction and records an edit reason.
4. `suggest_next_best_action`: recommends field-rep actions from recent HCP history.
5. `schedule_follow_up`: attaches a follow-up date and reason to the latest interaction.
6. `summarize_hcp_history`: summarizes recent activity for an HCP.

## Run Locally

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

The API will run at `http://127.0.0.1:8000`.

Set `GROQ_API_KEY` in `backend/.env` to use Groq. Without a key, the demo remains runnable through a deterministic local extraction fallback.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will run at `http://127.0.0.1:5173`.

If the backend runs somewhere else, create `frontend/.env`:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Demo Flow

1. Start the backend and frontend.
2. Click `Demo data` to seed HCP records.
3. On `Log HCP Interaction`, choose/search an HCP, confirm interaction details, add topics discussed, and submit `Log interaction`.
4. Use the `AI Assistant` panel and `AI Log` button with prompts such as:

```text
Find oncology HCPs
```

```text
What is the next best action?
```

```text
Schedule a follow up in 7 days.
```

```text
Summarize this HCP history.
```

```text
Edit the latest interaction summary to HCP requested access material and agreed to a follow-up discussion.
```

The LangGraph panel below the main screen shows which tools executed, and the timeline shows logged and edited interactions.

## Project Structure

```text
backend/
  app/
    agent/          LangGraph state graph and CRM tools
    api/            FastAPI routes
    core/           settings
    db/             SQLAlchemy engine/session
    services/       Groq LLM integration
  tests/            backend tests
docs/
  architecture.md   design notes
  demo_script.md    10-15 minute recording script
frontend/
  src/
    api/            API client
    components/     CRM UI panels
    features/       Redux CRM slice
```

## Verification

```bash
cd backend
pytest

cd ../frontend
npm run build
```
