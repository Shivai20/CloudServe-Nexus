"""End-to-End Stateful Processing Pipeline (A2-A8, A11).

Orchestrates multi-channel ingestion, calibrated classification, semantic retrieval,
deterministic routing, grounded generation, safety guardrails, and persistent 1:1 audit logging.
Ensures fault tolerance and graceful degradation under all failure modes.
"""

from typing import Any, Dict, List, Optional
import logging
import uuid
from src.classify import get_classifier
from src.generate import get_generator
from src.guardrails import get_guardrails
from src.ingest import normalize_ticket
from src.logging_store import get_logging_store
from src.models import (
    DecisionLogEntry,
    NormalizedTicket,
    ProcessedTicketOutput,
    RoutingAction,
)
from src.retrieve import get_retriever
from src.route import get_router

logger = logging.getLogger(__name__)


class SupportPipeline:
    """Stateful, auditable, deterministic support automation pipeline."""

    def __init__(self, threshold: Optional[float] = None):
        self.classifier = get_classifier()
        self.retriever = get_retriever()
        self.guardrails = get_guardrails()
        self.router = get_router(threshold=threshold) if threshold is not None else get_router()
        self.generator = get_generator()
        self.logger_store = get_logging_store()

    def process_ticket(self, raw_ticket: Dict[str, Any]) -> ProcessedTicketOutput:
        """Processes a single raw ticket end-to-end, producing output and logging a 1:1 audit entry."""
        decision_id = str(uuid.uuid4())

        try:
            # 1. Multi-Channel Ingestion (A2)
            ticket: NormalizedTicket = normalize_ticket(raw_ticket)

            # 2. Calibrated Intent & Urgency Classification (A3)
            classification = self.classifier.classify(ticket)

            # 3. Semantic Passage Retrieval (A4)
            retrieved_chunks = self.retriever.retrieve(ticket.full_text, top_k=3)

            # 4. Input Guardrails & Hard Redline Evaluation (A7)
            is_safe, guardrail_reason, guardrail_results = self.guardrails.check_input_ticket(
                ticket, classification.intent
            )

            # 5. Deterministic Routing Decision (A5)
            routing_decision = self.router.decide(ticket, classification, retrieved_chunks)

            # If input guardrail failed, override routing to escalate
            if not is_safe:
                routing_decision.action = RoutingAction.ESCALATE
                routing_decision.reason = f"Hard guardrail triggered: {guardrail_reason}"

            final_action = routing_decision.action
            response_text = None
            citations: List[str] = []

            # 6. Grounded Generation (A6) if auto_respond
            if final_action == RoutingAction.AUTO_RESPOND:
                gen_result = self.generator.generate(ticket, retrieved_chunks)
                
                # 7. Outbound Response Guardrail Check (A7)
                outbound_safe, out_reason, out_gr_results = self.guardrails.check_generated_response(
                    gen_result.response_text,
                    "\n".join(c.content for c in retrieved_chunks),
                )
                guardrail_results.update(out_gr_results)

                if outbound_safe:
                    response_text = gen_result.response_text
                    citations = gen_result.citations
                else:
                    logger.warning(f"Response blocked by outbound guardrail: {out_reason}")
                    final_action = RoutingAction.ESCALATE
                    routing_decision.reason = f"Response blocked by guardrail: {out_reason}"
                    response_text = None
                    citations = []

            # 8. Create 1:1 Audit Log Entry matching Governance Framework (A8)
            audit_entry = DecisionLogEntry(
                decision_id=decision_id,
                ticket_id=ticket.ticket_id,
                stage="routing" if final_action != RoutingAction.AUTO_RESPOND else "generation",
                input_summary=ticket.subject or ticket.body[:120],
                model={"name": "cloudserve-fde-pipeline", "version": "1.0"},
                prediction={
                    "value": classification.intent,
                    "confidence": classification.confidence,
                    "urgency": classification.urgency.value,
                },
                alternatives=[a.model_dump() for a in classification.alternatives],
                sources_used=[
                    {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                    for c in retrieved_chunks
                ],
                threshold_applied=routing_decision.threshold_applied,
                action_taken=final_action.value,
                reason=routing_decision.reason,
                guardrail_results=guardrail_results,
                prompt_version="PR-01 v1.0",
                requirement_ids=["FR-01", "FR-02", "FR-03", "FR-04", "FR-05", "FR-06", "FR-07"],
            )

            # Persist to 1:1 decision audit store
            self.logger_store.log_decision(audit_entry)

            return ProcessedTicketOutput(
                ticket_id=ticket.ticket_id,
                channel=ticket.channel.value,
                classified_intent=classification.intent,
                urgency=classification.urgency.value,
                confidence=classification.confidence,
                action=final_action.value,
                reason=routing_decision.reason,
                response_text=response_text,
                citations=citations,
                guardrails=guardrail_results,
                audit_log=audit_entry,
            )

        except Exception as e:
            # Resilient Fault Tolerance (A11) - never crash, degrade gracefully to safe escalation
            logger.error(f"Pipeline error on ticket {raw_ticket.get('ticket_id')}: {e}")
            t_id = str(raw_ticket.get("ticket_id") or "UNKNOWN")
            fallback_audit = DecisionLogEntry(
                decision_id=decision_id,
                ticket_id=t_id,
                stage="routing",
                input_summary="Pipeline error recovery",
                action_taken="escalate",
                reason=f"Graceful degradation on pipeline fault: {str(e)}",
                guardrail_results={"pii": "pass", "grounding": "pass", "tone": "pass"},
                requirement_ids=["FR-09", "FR-07"],
            )
            self.logger_store.log_decision(fallback_audit)

            return ProcessedTicketOutput(
                ticket_id=t_id,
                channel=str(raw_ticket.get("channel", "email")),
                classified_intent="unclear_request",
                urgency="medium",
                confidence=0.0,
                action="escalate",
                reason=f"System error handled gracefully: {str(e)}",
                response_text=None,
                citations=[],
                guardrails={"pii": "pass", "grounding": "pass", "tone": "pass"},
                audit_log=fallback_audit,
            )

    def process_batch(self, tickets: List[Dict[str, Any]]) -> List[ProcessedTicketOutput]:
        """Process a collection of tickets sequentially with strict 1:1 reconciliation."""
        return [self.process_ticket(t) for t in tickets]
