from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.core.config import get_settings


PRODUCT_CATALOG = [
    "CardioFlow",
    "GlucoTrack",
    "OncoRelief",
    "RespiraClear",
    "Immunex",
]


@dataclass
class LLMService:
    """Groq-backed extraction with a deterministic offline fallback for demos."""

    def _client(self):
        settings = get_settings()
        if not settings.groq_api_key:
            return None
        try:
            from groq import Groq
        except ImportError:
            return None
        return Groq(api_key=settings.groq_api_key)

    def extract_interaction(self, notes: str) -> dict:
        client = self._client()
        if client is None:
            return self._heuristic_extract(notes)

        settings = get_settings()
        prompt = (
            "Extract CRM interaction fields from the field rep note. "
            "Return only valid JSON with keys: summary, sentiment, intent, "
            "products_discussed, next_steps, objections."
        )
        try:
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": notes},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content or "{}"
            return self._normalize(json.loads(content), notes)
        except Exception:
            return self._heuristic_extract(notes)

    def draft_response(self, user_message: str, context: str) -> str:
        client = self._client()
        if client is None:
            return ""

        settings = get_settings()
        try:
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise life-sciences CRM copilot for field representatives.",
                    },
                    {"role": "user", "content": f"Context:\n{context}\n\nRequest:\n{user_message}"},
                ],
                temperature=0.35,
            )
            return completion.choices[0].message.content or ""
        except Exception:
            return ""

    def _heuristic_extract(self, notes: str) -> dict:
        clean = " ".join(notes.split())
        lower = clean.lower()
        products = [product for product in PRODUCT_CATALOG if product.lower() in lower]
        if not products:
            products = [word for word in PRODUCT_CATALOG[:2] if word[:5].lower() in lower]

        sentiment = "neutral"
        if any(token in lower for token in ["positive", "interested", "agreed", "open to", "requested"]):
            sentiment = "positive"
        if any(token in lower for token in ["concern", "hesitant", "objection", "too expensive", "not convinced"]):
            sentiment = "mixed"

        intent = "routine_follow_up"
        if any(token in lower for token in ["sample", "trial", "starter"]):
            intent = "sample_request"
        elif any(token in lower for token in [" formulary", "approval", "committee"]):
            intent = "access_discussion"
        elif any(token in lower for token in ["adverse", "side effect", "safety"]):
            intent = "medical_information_request"

        next_steps = self._sentences_matching(
            clean,
            ["follow", "send", "schedule", "share", "email", "call", "visit", "demo"],
        )
        objections = self._sentences_matching(
            clean,
            ["concern", "objection", "hesitant", "cost", "coverage", "safety", "side effect"],
        )

        summary = clean
        if len(summary) > 260:
            summary = summary[:257].rsplit(" ", 1)[0] + "..."

        return self._normalize(
            {
                "summary": summary,
                "sentiment": sentiment,
                "intent": intent,
                "products_discussed": products,
                "next_steps": next_steps or ["Confirm next follow-up window with the HCP."],
                "objections": objections,
            },
            notes,
        )

    def _sentences_matching(self, text: str, keywords: list[str]) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        matches = []
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                matches.append(sentence.strip())
        return matches[:4]

    def _normalize(self, payload: dict, notes: str) -> dict:
        return {
            "summary": str(payload.get("summary") or notes).strip(),
            "sentiment": str(payload.get("sentiment") or "neutral").strip().lower(),
            "intent": str(payload.get("intent") or "routine_follow_up").strip().lower(),
            "products_discussed": list(payload.get("products_discussed") or []),
            "next_steps": list(payload.get("next_steps") or []),
            "objections": list(payload.get("objections") or []),
        }

