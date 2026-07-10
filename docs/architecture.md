# Architecture

## Overview

The system is organized as a full-stack CRM workflow:

```text
React UI -> Redux thunks -> FastAPI routes -> LangGraph agent/tools -> SQL database
                                      |
                                      -> Groq LLM extraction service
```

The frontend gives the field representative two capture modes in one screen. The structured form is useful for precise data entry. The chat logger is useful when the rep wants to describe the visit naturally and let the AI agent convert it into CRM fields.

## Backend

FastAPI exposes endpoints for:

- HCP records.
- Interaction creation and editing.
- Agent chat.
- Demo data seeding.

SQLAlchemy models store HCPs and interactions. The backend reads `DATABASE_URL`, so it can use PostgreSQL for the assignment environment while still falling back to SQLite for a quick local demo.

## LangGraph Agent

The agent uses a small state graph:

```text
classify -> execute_tool -> respond
```

The classifier maps the rep message to a CRM intent. The executor calls the selected tool. The responder returns a concise user-facing response and exposes tool events to the frontend.

Tool calls are intentionally visible in the UI because the assignment asks for a demo of all tools working properly.

## LLM Usage

The `LLMService` calls Groq with the `gemma2-9b-it` model. It asks the model to return structured JSON containing:

- Summary.
- Sentiment.
- Intent.
- Products discussed.
- Next steps.
- Objections.

If a local reviewer has not configured `GROQ_API_KEY`, a deterministic heuristic fallback keeps the demo runnable. In production evaluation, configure Groq so the LLM path is active.

## Data Model

HCP fields:

- Name.
- Specialty.
- Organization.
- Territory.
- Priority.
- Last interaction date.

Interaction fields:

- Channel.
- Raw notes.
- Summary.
- Sentiment.
- Intent.
- Products discussed.
- Objections.
- Next steps.
- Follow-up date.
- Edit reason.

