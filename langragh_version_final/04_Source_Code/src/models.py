"""Pydantic v2 schemas for CloudServe Intelligent Support System.

Enforces strict type safety and schema validation across all stages:
- Multi-channel ingestion (A2)
- Intent & Urgency classification (A3)
- Passage retrieval (A4)
- Deterministic routing (A5)
- Grounded generation (A6)
- Guardrails (A7)
- 1:1 Decision audit logging (A8)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class TicketChannel(str, Enum):
    EMAIL = "email"
    CHAT = "chat"
    DOCS_COMMENT = "docs_comment"
    FORUM = "forum"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RoutingAction(str, Enum):
    AUTO_RESPOND = "auto_respond"
    ESCALATE = "escalate"
    BLOCK = "block"


class NormalizedTicket(BaseModel):
    ticket_id: str
    channel: TicketChannel
    subject: str = ""
    body: str
    received_at: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_tier: Optional[str] = "standard"
    customer_region: Optional[str] = None
    language_fluency: Optional[str] = "fluent"
    raw_data: Optional[Dict[str, Any]] = None

    @field_validator("body")
    @classmethod
    def sanitize_body(cls, v: str) -> str:
        if v is None:
            return ""
        return v.strip()

    @property
    def full_text(self) -> str:
        if self.subject and self.subject.strip():
            return f"{self.subject}\n\n{self.body}".strip()
        return self.body.strip()


class AlternativePrediction(BaseModel):
    value: str
    confidence: float


class ClassificationResult(BaseModel):
    intent: str
    urgency: UrgencyLevel
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives: List[AlternativePrediction] = Field(default_factory=list)


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    content: str
    category: Optional[str] = None
    score: float = 0.0


class RoutingDecision(BaseModel):
    action: RoutingAction
    reason: str
    threshold_applied: float
    confidence: float
    must_not_auto_respond: bool = False


class GuardrailCheck(BaseModel):
    pii: str = "pass"  # "pass" | "fail"
    grounding: str = "pass"  # "pass" | "fail"
    tone: str = "pass"  # "pass" | "fail"

    @property
    def all_passed(self) -> bool:
        return self.pii == "pass" and self.grounding == "pass" and self.tone == "pass"


class GenerationResult(BaseModel):
    response_text: str
    citations: List[str] = Field(default_factory=list)
    is_grounded: bool = True
    grounding_notes: Optional[str] = None


class DecisionLogEntry(BaseModel):
    decision_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ticket_id: str
    stage: str  # "classification" | "routing" | "generation" | "validation"
    input_summary: str
    model: Dict[str, str] = Field(default_factory=lambda: {"name": "deterministic-pipeline", "version": "1.0"})
    prediction: Dict[str, Any] = Field(default_factory=dict)
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    sources_used: List[Dict[str, Any]] = Field(default_factory=list)
    threshold_applied: float = 0.0
    action_taken: str  # "auto_respond" | "escalate" | "block"
    reason: str
    guardrail_results: Dict[str, str] = Field(default_factory=lambda: {"pii": "pass", "grounding": "pass", "tone": "pass"})
    prompt_version: str = "PR-01 v1.0"
    requirement_ids: List[str] = Field(default_factory=list)


class ProcessedTicketOutput(BaseModel):
    ticket_id: str
    channel: str
    classified_intent: str
    urgency: str
    confidence: float
    action: str  # "auto_respond" | "escalate" | "block"
    reason: str
    response_text: Optional[str] = None
    citations: List[str] = Field(default_factory=list)
    guardrails: Dict[str, str] = Field(default_factory=dict)
    audit_log: DecisionLogEntry
