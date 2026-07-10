from __future__ import annotations

import re
from typing import Any, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.agent.tools import (
    edit_interaction_tool,
    log_interaction_tool,
    schedule_follow_up_tool,
    search_hcp_tool,
    suggest_next_best_action_tool,
    summarize_hcp_history_tool,
)
from app.schemas import AgentResponse, InteractionCreate, InteractionOut, InteractionUpdate, ToolEvent
from app.services.llm import LLMService

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    END = "__end__"
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


class AgentState(TypedDict, total=False):
    db: Session
    llm: LLMService
    message: str
    hcp_id: int | None
    intent: str
    tool_events: list[dict[str, Any]]
    draft_interaction: models.Interaction | None
    suggestions: list[str]
    reply: str


def _classify(state: AgentState) -> AgentState:
    message = state["message"].lower()
    intent = "log_interaction"
    is_explicit_log = bool(re.search(r"\b(log|record|capture)\b", message))
    if is_explicit_log:
        intent = "log_interaction"
    elif any(token in message for token in ["search", "find", "look up"]):
        intent = "search_hcp"
    elif any(token in message for token in ["edit", "change", "correct", "update interaction"]):
        intent = "edit_interaction"
    elif any(token in message for token in ["next best", "recommend", "what should i do", "nba"]):
        intent = "suggest_next_best_action"
    elif any(token in message for token in ["follow up", "schedule", "remind"]):
        intent = "schedule_follow_up"
    elif any(token in message for token in ["summarize", "history", "recap"]):
        intent = "summarize_hcp_history"
    state["intent"] = intent
    state.setdefault("tool_events", [])
    state.setdefault("suggestions", [])
    return state


def _execute_tool(state: AgentState) -> AgentState:
    db = state["db"]
    llm = state["llm"]
    message = state["message"]
    hcp_id = state.get("hcp_id")
    intent = state["intent"]
    events = state.setdefault("tool_events", [])

    try:
        if intent == "search_hcp":
            query = _strip_command_words(message)
            result = search_hcp_tool(db, query)
            events.append({"name": "search_hcp", "status": "ok", "payload": result})

        elif intent == "edit_interaction":
            interaction_id = _interaction_id_from_text(message) or _latest_interaction_id(db, hcp_id)
            if interaction_id is None:
                events.append({"name": "edit_interaction", "status": "skipped", "payload": {"reason": "No interaction found."}})
            else:
                summary = _extract_after_keyword(message, ["summary to", "summary:"])
                update_payload = {"edited_reason": "Edited through CRM copilot chat."}
                if summary:
                    update_payload["summary"] = summary
                update = InteractionUpdate(**update_payload)
                updated = edit_interaction_tool(db, interaction_id, update)
                if updated:
                    state["draft_interaction"] = updated
                    events.append({"name": "edit_interaction", "status": "ok", "payload": {"interaction_id": updated.id}})

        elif intent == "suggest_next_best_action":
            if hcp_id is None:
                events.append({"name": "suggest_next_best_action", "status": "skipped", "payload": {"reason": "No HCP selected."}})
            else:
                result = suggest_next_best_action_tool(db, hcp_id)
                state["suggestions"] = result.get("actions", [])
                events.append({"name": "suggest_next_best_action", "status": "ok", "payload": result})

        elif intent == "schedule_follow_up":
            if hcp_id is None:
                events.append({"name": "schedule_follow_up", "status": "skipped", "payload": {"reason": "No HCP selected."}})
            else:
                days = _days_from_text(message)
                result = schedule_follow_up_tool(db, hcp_id=hcp_id, days_from_now=days, reason=message)
                events.append({"name": "schedule_follow_up", "status": "ok" if result.get("scheduled") else "skipped", "payload": result})

        elif intent == "summarize_hcp_history":
            if hcp_id is None:
                events.append({"name": "summarize_hcp_history", "status": "skipped", "payload": {"reason": "No HCP selected."}})
            else:
                result = summarize_hcp_history_tool(db, hcp_id)
                events.append({"name": "summarize_hcp_history", "status": "ok", "payload": result})

        else:
            if hcp_id is None:
                events.append({"name": "log_interaction", "status": "skipped", "payload": {"reason": "No HCP selected."}})
            else:
                interaction = log_interaction_tool(
                    db,
                    llm,
                    InteractionCreate(hcp_id=hcp_id, channel=_channel_from_text(message), raw_notes=message),
                )
                state["draft_interaction"] = interaction
                events.append({"name": "log_interaction", "status": "ok", "payload": {"interaction_id": interaction.id}})
                nba = suggest_next_best_action_tool(db, hcp_id)
                state["suggestions"] = nba.get("actions", [])
                events.append({"name": "suggest_next_best_action", "status": "ok", "payload": nba})
    except Exception as exc:
        events.append({"name": intent, "status": "error", "payload": {"detail": str(exc)}})

    return state


def _respond(state: AgentState) -> AgentState:
    events = state.get("tool_events", [])
    ok_events = [event for event in events if event.get("status") == "ok"]
    latest = ok_events[-1] if ok_events else events[-1] if events else None

    if latest is None:
        reply = "I could not identify a CRM action from that message."
    elif latest["name"] == "search_hcp":
        count = latest["payload"].get("count", 0)
        reply = f"I found {count} matching HCP record(s)."
    elif latest["name"] == "log_interaction":
        reply = "Interaction logged. I also generated next-best-action suggestions from the latest context."
    elif latest["name"] == "edit_interaction":
        reply = "Interaction updated and the audit reason was captured."
    elif latest["name"] == "schedule_follow_up":
        reply = "Follow-up scheduled and attached to the latest interaction."
    elif latest["name"] == "suggest_next_best_action":
        reply = "Here are the recommended next best actions."
    elif latest["name"] == "summarize_hcp_history":
        reply = latest["payload"].get("summary", "History summarized.")
    else:
        reply = latest.get("payload", {}).get("reason", "The requested action was skipped.")

    context = "\n".join(str(event) for event in events[-3:])
    llm_reply = state["llm"].draft_response(state["message"], context)
    state["reply"] = llm_reply.strip() or reply
    return state


def _build_graph():
    if not LANGGRAPH_AVAILABLE or StateGraph is None:
        return None
    graph = StateGraph(AgentState)
    graph.add_node("classify", _classify)
    graph.add_node("execute_tool", _execute_tool)
    graph.add_node("respond", _respond)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "execute_tool")
    graph.add_edge("execute_tool", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


class CRMAgent:
    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()
        self.graph = _build_graph()

    def invoke(self, db: Session, message: str, hcp_id: int | None = None) -> AgentResponse:
        state: AgentState = {"db": db, "llm": self.llm, "message": message, "hcp_id": hcp_id}
        if self.graph:
            result = self.graph.invoke(state)
        else:
            result = _respond(_execute_tool(_classify(state)))

        draft = result.get("draft_interaction")
        return AgentResponse(
            reply=result.get("reply", ""),
            tool_events=[ToolEvent(**event) for event in result.get("tool_events", [])],
            draft_interaction=InteractionOut.model_validate(draft) if draft is not None else None,
            suggestions=result.get("suggestions", []),
        )


def _strip_command_words(message: str) -> str:
    cleaned = re.sub(r"\b(search|find|look up|hcps?|doctors?|dr\.?)\b", "", message, flags=re.I)
    return re.sub(r"\s+", " ", cleaned).strip() or message


def _interaction_id_from_text(message: str) -> int | None:
    match = re.search(r"(?:interaction\s*#?|id\s*)(\d+)", message, flags=re.I)
    return int(match.group(1)) if match else None


def _latest_interaction_id(db: Session, hcp_id: int | None) -> int | None:
    if hcp_id is None:
        return None
    interaction = (
        db.execute(
            select(models.Interaction)
            .where(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.interaction_date.desc())
        )
        .scalars()
        .first()
    )
    return interaction.id if interaction else None


def _extract_after_keyword(message: str, keywords: list[str]) -> str:
    lowered = message.lower()
    for keyword in keywords:
        if keyword in lowered:
            return message[lowered.index(keyword) + len(keyword) :].strip(" .:")
    return ""


def _days_from_text(message: str) -> int:
    match = re.search(r"in\s+(\d+)\s+day", message, flags=re.I)
    if match:
        return max(1, int(match.group(1)))
    if "tomorrow" in message.lower():
        return 1
    if "next week" in message.lower():
        return 7
    return 7


def _channel_from_text(message: str) -> str:
    lowered = message.lower()
    for channel in ["email", "phone", "video", "conference", "chat"]:
        if channel in lowered:
            return channel
    return "in_person"
