from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.schemas import InteractionCreate, InteractionUpdate
from app.services.llm import LLMService


def search_hcp_tool(db: Session, query: str) -> dict[str, Any]:
    term = f"%{query.strip()}%"
    stmt = (
        select(models.HCP)
        .where(
            models.HCP.name.ilike(term)
            | models.HCP.specialty.ilike(term)
            | models.HCP.organization.ilike(term)
            | models.HCP.territory.ilike(term)
        )
        .limit(8)
    )
    hcps = db.execute(stmt).scalars().all()
    return {
        "count": len(hcps),
        "results": [
            {
                "id": hcp.id,
                "name": hcp.name,
                "specialty": hcp.specialty,
                "organization": hcp.organization,
                "priority": hcp.priority,
            }
            for hcp in hcps
        ],
    }


def log_interaction_tool(
    db: Session,
    llm: LLMService,
    interaction: InteractionCreate,
) -> models.Interaction:
    extracted = llm.extract_interaction(interaction.raw_notes)
    summary = interaction.summary or extracted["summary"]
    sentiment = interaction.sentiment or extracted["sentiment"]
    intent = interaction.intent or extracted["intent"]

    db_interaction = models.Interaction(
        hcp_id=interaction.hcp_id,
        channel=interaction.channel,
        interaction_date=interaction.interaction_date or datetime.now(timezone.utc),
        raw_notes=interaction.raw_notes,
        summary=summary,
        sentiment=sentiment,
        intent=intent,
        products_discussed=interaction.products_discussed or extracted["products_discussed"],
        next_steps=interaction.next_steps or extracted["next_steps"],
        objections=interaction.objections or extracted["objections"],
        follow_up_date=interaction.follow_up_date,
        status="logged",
    )
    db.add(db_interaction)

    hcp = db.get(models.HCP, interaction.hcp_id)
    if hcp:
        hcp.last_interaction_at = db_interaction.interaction_date

    db.commit()
    db.refresh(db_interaction)
    return db_interaction


def edit_interaction_tool(
    db: Session,
    interaction_id: int,
    update: InteractionUpdate,
) -> models.Interaction | None:
    interaction = db.get(models.Interaction, interaction_id)
    if interaction is None:
        return None

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(interaction, key, value)
    interaction.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(interaction)
    return interaction


def suggest_next_best_action_tool(db: Session, hcp_id: int) -> dict[str, Any]:
    interactions = (
        db.execute(
            select(models.Interaction)
            .where(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.interaction_date.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )
    hcp = db.get(models.HCP, hcp_id)
    if hcp is None:
        return {"actions": ["Select a valid HCP before requesting next best actions."]}

    if not interactions:
        return {
            "actions": [
                f"Prepare an opening call plan for {hcp.name}.",
                "Confirm specialty focus, patient volume, and access constraints.",
                "Capture preferred channel and best follow-up cadence.",
            ]
        }

    latest = interactions[0]
    actions = []
    if latest.objections:
        actions.append("Send evidence or access support that directly addresses the recorded objection.")
    if latest.sentiment == "positive":
        actions.append("Advance the discussion with a concrete next step and confirmed date.")
    if latest.follow_up_date is None:
        actions.append("Schedule a follow-up while the interaction context is still fresh.")
    if latest.products_discussed:
        products = ", ".join(latest.products_discussed)
        actions.append(f"Share tailored clinical or access material for {products}.")
    actions.append("Update the account plan with learning from the latest interaction.")
    return {"actions": actions[:4], "based_on_interaction_id": latest.id}


def schedule_follow_up_tool(
    db: Session,
    hcp_id: int,
    interaction_id: int | None = None,
    days_from_now: int = 7,
    reason: str = "Follow-up scheduled by CRM copilot.",
) -> dict[str, Any]:
    due_at = datetime.now(timezone.utc) + timedelta(days=days_from_now)
    interaction = None
    if interaction_id:
        interaction = db.get(models.Interaction, interaction_id)
    if interaction is None:
        interaction = (
            db.execute(
                select(models.Interaction)
                .where(models.Interaction.hcp_id == hcp_id)
                .order_by(models.Interaction.interaction_date.desc())
            )
            .scalars()
            .first()
        )
    if interaction is None:
        return {"scheduled": False, "reason": "No interaction is available to attach the follow-up."}

    next_steps = list(interaction.next_steps or [])
    if reason not in next_steps:
        next_steps.append(reason)
    interaction.next_steps = next_steps
    interaction.follow_up_date = due_at
    interaction.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "scheduled": True,
        "interaction_id": interaction.id,
        "follow_up_date": due_at.isoformat(),
        "reason": reason,
    }


def summarize_hcp_history_tool(db: Session, hcp_id: int) -> dict[str, Any]:
    hcp = db.get(models.HCP, hcp_id)
    if hcp is None:
        return {"summary": "No HCP selected."}
    interactions = (
        db.execute(
            select(models.Interaction)
            .where(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.interaction_date.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )
    if not interactions:
        return {"summary": f"{hcp.name} has no logged interactions yet."}

    themes = sorted({item.intent for item in interactions})
    products = sorted({product for item in interactions for product in (item.products_discussed or [])})
    return {
        "summary": (
            f"{hcp.name} has {len(interactions)} recent interaction(s). "
            f"Common intents: {', '.join(themes) or 'none yet'}. "
            f"Products discussed: {', '.join(products) or 'none captured'}."
        ),
        "latest_interaction_id": interactions[0].id,
    }


CRM_TOOLS = {
    "search_hcp": search_hcp_tool,
    "log_interaction": log_interaction_tool,
    "edit_interaction": edit_interaction_tool,
    "suggest_next_best_action": suggest_next_best_action_tool,
    "schedule_follow_up": schedule_follow_up_tool,
    "summarize_hcp_history": summarize_hcp_history_tool,
}

