"""Deterministic Routing Engine (A5).

Employs empirical confidence thresholds and hard safety gates (must_not_auto_respond)
to route tickets deterministically to either 'auto_respond' or 'escalate'.
Identical inputs strictly produce identical routing decisions.
"""

from typing import Any, Dict, List, Optional
import json
import logging
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from src.guardrails import get_guardrails
from src.models import (
    ClassificationResult,
    NormalizedTicket,
    RetrievedChunk,
    RoutingAction,
    RoutingDecision,
)

logger = logging.getLogger(__name__)

DEFAULT_DEV_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "development_tickets.json"
)
DEFAULT_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))


class RoutingEngine:
    """Deterministic routing engine that balances automation rate with zero safety violations."""

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        dev_data_path: str = DEFAULT_DEV_DATA_PATH,
    ):
        self.threshold = threshold
        self.dev_data_path = dev_data_path
        self.guardrails = get_guardrails()
        self.model: Optional[Pipeline] = None
        self._train_routing_classifier()

    def _train_routing_classifier(self):
        """Trains an empirical routing model on development ticket patterns."""
        if not os.path.exists(self.dev_data_path):
            logger.warning(f"Training data not found at {self.dev_data_path}")
            return

        with open(self.dev_data_path, "r", encoding="utf-8") as f:
            tickets = json.load(f)

        features = []
        labels = []
        for t in tickets:
            intent = t.get("labels", {}).get("intent", "")
            tier = t.get("customer_tier", "standard")
            subj = str(t.get("subject", "") or "")
            body = str(t.get("body", "") or "")
            expected_route = t.get("labels", {}).get("expected_route", "escalate")

            feat_str = f"intent:{intent} tier:{tier} {subj} {body}".strip()
            features.append(feat_str)
            labels.append(expected_route)

        if features and labels:
            self.model = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
                ("clf", LogisticRegression(C=5.0, max_iter=1000, random_state=42)),
            ])
            self.model.fit(features, labels)
            logger.info("Empirical routing engine trained.")

    def decide(
        self,
        ticket: NormalizedTicket,
        classification: ClassificationResult,
        retrieved_chunks: List[RetrievedChunk],
    ) -> RoutingDecision:
        """Determines routing action: 'auto_respond' or 'escalate' deterministically."""
        # 1. HARD SAFETY GATE: Input Guardrails & Redlines
        is_safe, guardrail_reason, _ = self.guardrails.check_input_ticket(
            ticket, classification.intent
        )
        if not is_safe:
            return RoutingDecision(
                action=RoutingAction.ESCALATE,
                reason=f"Mandatory escalation triggered by safety redline: {guardrail_reason}",
                threshold_applied=self.threshold,
                confidence=classification.confidence,
                must_not_auto_respond=True,
            )

        # 2. DOCUMENTATION AVAILABILITY GATE: Must have retrieved passages
        if not retrieved_chunks:
            return RoutingDecision(
                action=RoutingAction.ESCALATE,
                reason="Escalated: No authoritative documentation passages found in knowledge base.",
                threshold_applied=self.threshold,
                confidence=classification.confidence,
                must_not_auto_respond=False,
            )

        # 3. EMPIRICAL ROUTING PREDICTION & THRESHOLD GATE
        # We strictly use the calibrated classification confidence against the operational threshold tau (0.55).
        # We do not override it with a secondary model to ensure Low-Confidence intents are properly escalated.
        auto_confidence = classification.confidence

        if auto_confidence >= self.threshold:
            return RoutingDecision(
                action=RoutingAction.AUTO_RESPOND,
                reason=(
                    f"Passed all safety gates and retrieved authoritative documentation. "
                    f"Confidence score ({auto_confidence:.2f}) meets operational threshold ({self.threshold:.2f})."
                ),
                threshold_applied=self.threshold,
                confidence=auto_confidence,
                must_not_auto_respond=False,
            )
        else:
            return RoutingDecision(
                action=RoutingAction.ESCALATE,
                reason=(
                    f"Escalated: Routing confidence score ({auto_confidence:.2f}) fell below "
                    f"operational threshold ({self.threshold:.2f}). Routed to human specialist."
                ),
                threshold_applied=self.threshold,
                confidence=auto_confidence,
                must_not_auto_respond=False,
            )


_router_instance: Optional[RoutingEngine] = None


def get_router(threshold: float = DEFAULT_THRESHOLD) -> RoutingEngine:
    global _router_instance
    if _router_instance is None:
        _router_instance = RoutingEngine(threshold=threshold)
    return _router_instance
