from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Channel = Literal["in_person", "phone", "email", "video", "conference", "chat"]


class HCPCreate(BaseModel):
    name: str
    specialty: str
    organization: str
    territory: str
    priority: Literal["High", "Medium", "Low"] = "Medium"


class HCPOut(HCPCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_interaction_at: datetime | None = None
    created_at: datetime


class InteractionCreate(BaseModel):
    hcp_id: int
    channel: Channel = "in_person"
    interaction_date: datetime | None = None
    raw_notes: str = Field(min_length=5)
    summary: str | None = None
    sentiment: str | None = None
    intent: str | None = None
    products_discussed: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    follow_up_date: datetime | None = None


class InteractionUpdate(BaseModel):
    channel: Channel | None = None
    raw_notes: str | None = None
    summary: str | None = None
    sentiment: str | None = None
    intent: str | None = None
    products_discussed: list[str] | None = None
    next_steps: list[str] | None = None
    objections: list[str] | None = None
    status: str | None = None
    follow_up_date: datetime | None = None
    edited_reason: str | None = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hcp_id: int
    channel: str
    interaction_date: datetime
    raw_notes: str
    summary: str
    sentiment: str
    intent: str
    products_discussed: list[str]
    next_steps: list[str]
    objections: list[str]
    status: str
    follow_up_date: datetime | None = None
    edited_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=2)
    hcp_id: int | None = None
    conversation: list[ChatMessage] = Field(default_factory=list)


class ToolEvent(BaseModel):
    name: str
    status: Literal["ok", "skipped", "error"] = "ok"
    payload: dict = Field(default_factory=dict)


class AgentResponse(BaseModel):
    reply: str
    tool_events: list[ToolEvent] = Field(default_factory=list)
    draft_interaction: InteractionOut | None = None
    suggestions: list[str] = Field(default_factory=list)

