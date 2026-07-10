# AI-First CRM HCP Module

Full-stack AI-first Healthcare Professional (HCP) CRM application built with **React**, **Redux Toolkit**, **FastAPI**, **LangGraph**, and **Groq LLM**.

This project allows Medical Representatives to log HCP interactions using both a structured form and an AI-powered assistant.

---

# Features

## HCP Management
- Search Healthcare Professionals
- Territory-wise listing
- Priority (High / Medium / Low)
- Organization & Specialty details

## Interaction Logging
- Structured interaction form
- Interaction Type
- Date & Time
- Attendees
- Topics Discussed
- Materials Shared
- Products Discussed
- Next Steps
- Edit Latest Interaction

## AI Assistant
- AI Log Interaction
- Search HCP
- Edit Interaction
- Next Best Action
- Schedule Follow-up
- Summarize HCP History

## Timeline
- View all interactions
- Follow-up history
- Sentiment
- Products discussed
- Interaction summaries

---

# Tech Stack

## Frontend
- React
- Redux Toolkit
- Vite
- Axios
- CSS

## Backend
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- PostgreSQL Ready

## AI
- LangGraph
- Groq LLM
- Gemma2-9B-it

---

# Project Structure

```
ai-first-crm-hcp-module/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── run_dev.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   ├── architecture.md
│   └── demo_script.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# Backend Setup

```bash
cd backend

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env

uvicorn app.main:app --reload
```

Backend runs on

```
http://127.0.0.1:8000
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

# Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on

```
http://localhost:5173
```

If required create

```
frontend/.env
```

```
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

---

# AI Agent Tools

The project includes six LangGraph powered CRM tools.

- Search HCP
- Log Interaction
- Edit Interaction
- Next Best Action
- Schedule Follow-up
- Summarize HCP History

---

# Demo Workflow

1. Start Backend
2. Start Frontend
3. Click **Demo Data**
4. Select an HCP
5. Fill the interaction form
6. Click **Log Interaction**
7. Use AI Assistant
8. View updated Timeline
9. Test APIs using Swagger

---

# API Endpoints

```
GET    /api/health

POST   /api/seed

GET    /api/hcps

POST   /api/hcps

GET    /api/interactions

POST   /api/interactions

PATCH  /api/interactions/{interaction_id}

POST   /api/agent/chat

POST   /api/agent/next-best-action
```

---

# Verification

Backend

```bash
cd backend

pytest
```

Frontend

```bash
cd frontend

npm run build
```

---

# Author

**Zahir Ahmed Patel**

GitHub

https://github.com/build-with-zahir

Repository

https://github.com/build-with-zahir/ai-first-crm-hcp-module

---

# License

This project was developed as an AI-First CRM HCP Module assignment using React, FastAPI, LangGraph, Redux Toolkit and Groq LLM.
