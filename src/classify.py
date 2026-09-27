"""Calibrated Intent & Urgency Classification Module (A3).

Assigns an intent category (from 22 valid intents) and an urgency level (low/medium/high)
with a calibrated numeric confidence score in [0.0, 1.0], recording considered alternatives.
Includes resilient fallback on malformed input or provider timeouts (A11).
"""

from typing import Any, Dict, List, Optional
import json
import logging
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from src.models import (
    AlternativePrediction,
    ClassificationResult,
    NormalizedTicket,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)

# The 22 Canonical Intent Classes
VALID_INTENTS = [
    "account_access",
    "api_key_issue",
    "api_usage_question",
    "authentication_failure",
    "billing_query",
    "compliance_request",
    "configuration_help",
    "data_export",
    "data_residency",
    "database_issue",
    "deployment_failure",
    "feature_request",
    "integration_help",
    "onboarding",
    "performance_degradation",
    "quota_or_overage",
    "rate_limit",
    "rollback_request",
    "security_incident",
    "sso_configuration",
    "unclear_request",
    "webhook_issue",
]

DEFAULT_DEV_TICKETS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "development_tickets.json"
)

# Intent to baseline urgency mapping
INTENT_URGENCY_MAP = {
    "security_incident": UrgencyLevel.HIGH,
    "rollback_request": UrgencyLevel.HIGH,
    "deployment_failure": UrgencyLevel.HIGH,
    "database_issue": UrgencyLevel.HIGH,
    "authentication_failure": UrgencyLevel.HIGH,
    "api_key_issue": UrgencyLevel.MEDIUM,
    "performance_degradation": UrgencyLevel.MEDIUM,
    "rate_limit": UrgencyLevel.MEDIUM,
    "quota_or_overage": UrgencyLevel.MEDIUM,
    "data_export": UrgencyLevel.MEDIUM,
    "data_residency": UrgencyLevel.MEDIUM,
    "compliance_request": UrgencyLevel.MEDIUM,
    "billing_query": UrgencyLevel.MEDIUM,
    "sso_configuration": UrgencyLevel.MEDIUM,
    "account_access": UrgencyLevel.MEDIUM,
    "webhook_issue": UrgencyLevel.MEDIUM,
    "integration_help": UrgencyLevel.LOW,
    "configuration_help": UrgencyLevel.LOW,
    "api_usage_question": UrgencyLevel.LOW,
    "onboarding": UrgencyLevel.LOW,
    "feature_request": UrgencyLevel.LOW,
    "unclear_request": UrgencyLevel.LOW,
}


class IntentClassifier:
    """Deterministic, calibrated classifier with offline fallback and LLM support."""

    def __init__(self, dev_data_path: str = DEFAULT_DEV_TICKETS_PATH):
        self.dev_data_path = dev_data_path
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        base_lr = LogisticRegression(C=5.0, max_iter=1000, random_state=42)
        self.model = CalibratedClassifierCV(estimator=base_lr, cv=3)
        self.is_trained = False
        self._train_from_data()

    def _train_from_data(self):
        """Trains the calibrated intent model on development tickets."""
        if not os.path.exists(self.dev_data_path):
            logger.warning(f"Training data not found at {self.dev_data_path}")
            return

        with open(self.dev_data_path, "r", encoding="utf-8") as f:
            tickets = json.load(f)

        texts = []
        labels = []
        for t in tickets:
            subj = str(t.get("subject", "") or "")
            body = str(t.get("body", "") or "")
            text = f"{subj} {body}".strip()
            label = t.get("labels", {}).get("intent")
            if text and label and label in VALID_INTENTS:
                texts.append(text)
                labels.append(label)

        if texts and labels:
            X = self.vectorizer.fit_transform(texts)
            self.model.fit(X, labels)
            self.is_trained = True
            logger.info(f"Classifier trained on {len(texts)} tickets across {len(set(labels))} intents.")

    def classify(self, ticket: NormalizedTicket) -> ClassificationResult:
        """Classifies a ticket's intent and urgency, returning calibrated confidences and alternatives."""
        try:
            full_text = ticket.full_text
            if not full_text or not self.is_trained:
                # Return defined fallback per A3 & A11
                return ClassificationResult(
                    intent="unclear_request",
                    urgency=UrgencyLevel.LOW,
                    confidence=0.5,
                    alternatives=[],
                )

            X = self.vectorizer.transform([full_text])
            probabilities = self.model.predict_proba(X)[0]
            classes = self.model.classes_

            # Sort predictions descending
            sorted_indices = probabilities.argsort()[::-1]
            top_idx = sorted_indices[0]
            top_intent = classes[top_idx]
            top_confidence = float(probabilities[top_idx])

            # Gather top alternatives
            alternatives = []
            for idx in sorted_indices[1:4]:
                alternatives.append(
                    AlternativePrediction(
                        value=str(classes[idx]),
                        confidence=round(float(probabilities[idx]), 4),
                    )
                )

            # Determine urgency based on intent and customer tier
            urgency = self._determine_urgency(ticket, top_intent)

            return ClassificationResult(
                intent=str(top_intent),
                urgency=urgency,
                confidence=round(top_confidence, 4),
                alternatives=alternatives,
            )

        except Exception as e:
            logger.error(f"Error during classification: {e}. Returning safe fallback.")
            return ClassificationResult(
                intent="unclear_request",
                urgency=UrgencyLevel.MEDIUM,
                confidence=0.5,
                alternatives=[],
            )

    def _determine_urgency(self, ticket: NormalizedTicket, intent: str) -> UrgencyLevel:
        """Determines calibrated urgency based on intent and metadata."""
        base_urgency = INTENT_URGENCY_MAP.get(intent, UrgencyLevel.MEDIUM)
        
        # Enterprise customers with outage/critical requests escalate urgency
        text_lower = ticket.full_text.lower()
        if ticket.customer_tier == "enterprise" and (
            "down" in text_lower or "outage" in text_lower or "critical" in text_lower
        ):
            return UrgencyLevel.HIGH

        if base_urgency == UrgencyLevel.HIGH:
            return UrgencyLevel.HIGH
        elif base_urgency == UrgencyLevel.LOW and ticket.customer_tier != "enterprise":
            return UrgencyLevel.LOW
        return UrgencyLevel.MEDIUM


_classifier_instance: Optional[IntentClassifier] = None


def get_classifier(dev_data_path: str = DEFAULT_DEV_TICKETS_PATH) -> IntentClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier(dev_data_path=dev_data_path)
    return _classifier_instance


def classify_ticket(ticket: NormalizedTicket) -> ClassificationResult:
    return get_classifier().classify(ticket)
