from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(140), nullable=False, index=True)
    specialty = Column(String(120), nullable=False)
    organization = Column(String(180), nullable=False)
    territory = Column(String(120), nullable=False)
    priority = Column(String(20), nullable=False, default="Medium")
    last_interaction_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    interactions = relationship(
        "Interaction",
        back_populates="hcp",
        cascade="all, delete-orphan",
        order_by="desc(Interaction.interaction_date)",
    )


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False, index=True)
    channel = Column(String(40), nullable=False)
    interaction_date = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    raw_notes = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    sentiment = Column(String(30), nullable=False, default="neutral")
    intent = Column(String(80), nullable=False, default="routine_follow_up")
    products_discussed = Column(JSON, nullable=False, default=list)
    next_steps = Column(JSON, nullable=False, default=list)
    objections = Column(JSON, nullable=False, default=list)
    status = Column(String(40), nullable=False, default="logged")
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    edited_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    hcp = relationship("HCP", back_populates="interactions")

