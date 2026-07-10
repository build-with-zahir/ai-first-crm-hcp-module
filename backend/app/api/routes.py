from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.agent.graph import CRMAgent
from app.agent.tools import edit_interaction_tool, log_interaction_tool
from app.db.session import get_db
from app.schemas import (
    AgentResponse,
    ChatRequest,
    HCPCreate,
    HCPOut,
    InteractionCreate,
    InteractionOut,
    InteractionUpdate,
)
from app.services.llm import LLMService


router = APIRouter()
agent = CRMAgent(LLMService())


SAMPLE_HCPS = [
    HCPCreate(
        name="Dr. Ananya Rao",
        specialty="Cardiology",
        organization="Apex Heart Institute",
        territory="Bengaluru Central",
        priority="High",
    ),
    HCPCreate(
        name="Dr. Michael Chen",
        specialty="Endocrinology",
        organization="Northside Medical Group",
        territory="Mumbai West",
        priority="Medium",
    ),
    HCPCreate(
        name="Dr. Sara Kapoor",
        specialty="Oncology",
        organization="Metro Cancer Centre",
        territory="Delhi NCR",
        priority="High",
    ),
]


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@router.post("/seed", response_model=list[HCPOut])
def seed_demo_data(db: Session = Depends(get_db)) -> list[models.HCP]:
    existing = db.execute(select(models.HCP)).scalars().all()
    if not existing:
        for sample in SAMPLE_HCPS:
            db.add(models.HCP(**sample.model_dump()))
        db.commit()
    return db.execute(select(models.HCP).order_by(models.HCP.priority, models.HCP.name)).scalars().all()


@router.get("/hcps", response_model=list[HCPOut])
def list_hcps(db: Session = Depends(get_db)) -> list[models.HCP]:
    return db.execute(select(models.HCP).order_by(models.HCP.name)).scalars().all()


@router.post("/hcps", response_model=HCPOut)
def create_hcp(payload: HCPCreate, db: Session = Depends(get_db)) -> models.HCP:
    hcp = models.HCP(**payload.model_dump())
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp


@router.get("/interactions", response_model=list[InteractionOut])
def list_interactions(hcp_id: int | None = None, db: Session = Depends(get_db)) -> list[models.Interaction]:
    stmt = select(models.Interaction).order_by(models.Interaction.interaction_date.desc())
    if hcp_id is not None:
        stmt = stmt.where(models.Interaction.hcp_id == hcp_id)
    return db.execute(stmt).scalars().all()


@router.post("/interactions", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)) -> models.Interaction:
    if db.get(models.HCP, payload.hcp_id) is None:
        raise HTTPException(status_code=404, detail="HCP not found")
    return log_interaction_tool(db, LLMService(), payload)


@router.patch("/interactions/{interaction_id}", response_model=InteractionOut)
def update_interaction(
    interaction_id: int,
    payload: InteractionUpdate,
    db: Session = Depends(get_db),
) -> models.Interaction:
    updated = edit_interaction_tool(db, interaction_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return updated


@router.post("/agent/chat", response_model=AgentResponse)
def chat_with_agent(payload: ChatRequest, db: Session = Depends(get_db)) -> AgentResponse:
    if payload.hcp_id is not None and db.get(models.HCP, payload.hcp_id) is None:
        raise HTTPException(status_code=404, detail="HCP not found")
    return agent.invoke(db, payload.message, payload.hcp_id)

@router.post("/agent/next-best-action")
def next_best_action(payload: dict):
    priority = payload.get("priority", "Medium")
    specialty = payload.get("specialty", "")

    actions = []

    if priority.lower() == "high":
        actions.append("Schedule follow-up within 3 days")
        actions.append("Share latest clinical outcomes")

    if specialty.lower() == "cardiology":
        actions.append("Recommend CardioFlow brochure")

    elif specialty.lower() == "oncology":
        actions.append("Share Oncology case studies")

    elif specialty.lower() == "endocrinology":
        actions.append("Share Diabetes management guide")

    actions.append("Invite doctor to webinar")
    actions.append("Collect feedback")

    return {
        "actions": actions
    }