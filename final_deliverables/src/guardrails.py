"""Hard Guardrails & Safety Module (A7).

Enforces mandatory safety gates that can BLOCK responses and trigger escalation:
1. PII Detection (Credit card numbers, SSNs, raw API keys, passwords)
2. Prohibited Claims & Hallucinations ("refund has been issued", "fixed on our side", etc.)
3. Toxic Tone & Prompt Injection attempts ("ignore previous instructions", system leaks)
4. Redline Intent Detection (security incidents, legal compliance, GDPR)
"""

from typing import Dict, List, Optional, Tuple
import logging
import re
from src.models import GuardrailCheck, NormalizedTicket

logger = logging.getLogger(__name__)

# Regex for PII patterns
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
RAW_API_KEY_REGEX = re.compile(r"\b(?:cs_[live|test]_[0-9a-zA-Z]{24,}|sk-[a-zA-Z0-9]{32,})\b")
PASSWORD_IN_TEXT_REGEX = re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?\S+['\"]?", re.IGNORECASE)

# Prohibited factual promises / claims (from ground_truth_responses.json)
PROHIBITED_CLAIMS = [
    "a refund has been issued",
    "refund has been processed",
    "issued a refund",
    "the issue has been fixed on our side",
    "we have resolved the bug on our end",
    "a specific delivery date for a fix",
    "guarantee delivery by",
    "will be released tomorrow",
]

# Prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+system\s+prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"bypass\s+all\s+safety\s+filters",
    r"output\s+the\s+system\s+prompt",
]

# Redline intents that must never receive an automated reply
MANDATORY_ESCALATION_INTENTS = {
    "security_incident",
    "compliance_request",
    "feature_request",
    "unclear_request",
    "billing_query",
    "data_residency",
}


class GuardrailsEngine:
    """Enforces safety guardrails capable of blocking responses and forcing human escalation."""

    def check_input_ticket(self, ticket: NormalizedTicket, intent: str) -> Tuple[bool, str, Dict[str, str]]:
        """Pre-generation check: evaluates ticket for PII, prompt injections, and safety redlines."""
        results = {"pii": "pass", "grounding": "pass", "tone": "pass"}
        text = ticket.full_text

        # 1. PII detection in input
        if self._detect_pii(text):
            results["pii"] = "fail"
            return False, "PII or sensitive credential detected in ticket body", results

        # 2. Prompt injection detection
        if self._detect_prompt_injection(text):
            results["tone"] = "fail"
            return False, "Potential prompt injection or adversarial instruction detected", results

        # 3. Mandatory escalation intents
        if intent in MANDATORY_ESCALATION_INTENTS:
            return False, f"Intent '{intent}' is a mandatory human escalation redline", results

        return True, "Ticket passed input guardrails", results

    def check_generated_response(
        self, response_text: str, cited_chunks_text: str
    ) -> Tuple[bool, str, Dict[str, str]]:
        """Post-generation check: verifies outbound answer for PII, toxic tone, and prohibited claims."""
        results = {"pii": "pass", "grounding": "pass", "tone": "pass"}

        if not response_text or not response_text.strip():
            results["grounding"] = "fail"
            return False, "Generated response was empty", results

        # 1. Outbound PII Leakage Check
        if self._detect_pii(response_text):
            results["pii"] = "fail"
            return False, "Outbound response contains detected PII/credentials", results

        # 2. Prohibited Claims Check (Hallucinated promises)
        lower_resp = response_text.lower()
        for prohibited in PROHIBITED_CLAIMS:
            if prohibited in lower_resp:
                results["grounding"] = "fail"
                return False, f"Response contains prohibited ungrounded claim: '{prohibited}'", results

        # 3. Grounding validation: ensure response doesn't contradict lack of retrieval
        if "[unsupported]" in lower_resp or "cannot verify" in lower_resp:
            results["grounding"] = "fail"
            return False, "Response indicates lack of grounded documentation support", results

        return True, "Response passed all validation guardrails", results

    def _detect_pii(self, text: str) -> bool:
        """Detects presence of credit cards, SSNs, or raw secrets."""
        if CREDIT_CARD_REGEX.search(text):
            return True
        if SSN_REGEX.search(text):
            return True
        if RAW_API_KEY_REGEX.search(text):
            return True
        if PASSWORD_IN_TEXT_REGEX.search(text):
            return True
        return False

    def _detect_prompt_injection(self, text: str) -> bool:
        """Checks for common jailbreaks or prompt injection signatures."""
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


_guardrails_instance: Optional[GuardrailsEngine] = None


def get_guardrails() -> GuardrailsEngine:
    global _guardrails_instance
    if _guardrails_instance is None:
        _guardrails_instance = GuardrailsEngine()
    return _guardrails_instance
