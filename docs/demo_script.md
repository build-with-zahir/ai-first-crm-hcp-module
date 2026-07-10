# 10-15 Minute Video Script

## 1. Task Understanding

Explain that the goal is an AI-first CRM module for life-sciences field representatives, focused on logging HCP interactions either through a structured form or a conversational interface.

## 2. Frontend Walkthrough

Show:

- The video-matched `Log HCP Interaction` screen.
- HCP search/name, interaction type, date/time, attendees, topics discussed, voice-note consent, and materials/samples fields.
- The right-side `AI Assistant` chat panel and blue `AI Log` button.
- LangGraph tool panel.
- Next-step suggestions.
- Interaction timeline.

## 3. Structured Logging Demo

Select/search an HCP, edit `Topics Discussed`, optionally add materials/samples, and submit `Log interaction`. Point out that the interaction appears in the timeline and that extracted next steps appear in the suggestions panel.

## 4. Conversational Logging Demo

Use this prompt:

```text
Log a phone call: HCP was positive about GlucoTrack, raised a coverage concern, and asked for patient education material.
```

Show the `log_interaction` and `suggest_next_best_action` tool events.

## 5. Tool Demo

Run these prompts to demonstrate the remaining tools:

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

## 6. Backend and Code Structure

Open `/docs` on FastAPI and show:

- `/api/hcps`
- `/api/interactions`
- `/api/agent/chat`

Then briefly show:

- `backend/app/agent/graph.py`
- `backend/app/agent/tools.py`
- `backend/app/services/llm.py`
- `frontend/src/features/crmSlice.js`
- `frontend/src/components`

## 7. Closing Summary

Summarize that the project meets the requirements: React and Redux frontend, FastAPI backend, LangGraph agent, Groq LLM model, PostgreSQL-ready persistence, and more than five CRM tools.
