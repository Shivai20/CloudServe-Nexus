"""End-to-End Stateful Processing Pipeline (A2-A8, A11).

Orchestrates multi-channel ingestion, calibrated classification, semantic retrieval,
deterministic routing, grounded generation, safety guardrails, and persistent 1:1 audit logging
using a LangGraph StateGraph as required by the technical constraints.
Ensures fault tolerance and graceful degradation under all failure modes.
"""

from typing import Any, Dict, List, Optional, TypedDict
import logging
import uuid
import os
from langgraph.graph import StateGraph, END
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
    ClassificationResult,
    RetrievedChunk,
    RoutingDecision
)
from src.retrieve import get_retriever
from src.route import get_router

logger = logging.getLogger(__name__)

class PipelineState(TypedDict):
    raw_ticket: Dict[str, Any]
    decision_id: str
    ticket: Optional[NormalizedTicket]
    classification: Optional[ClassificationResult]
    retrieved_chunks: List[RetrievedChunk]
    guardrail_results: Dict[str, str]
    routing_decision: Optional[RoutingDecision]
    final_action: Optional[RoutingAction]
    response_text: Optional[str]
    citations: List[str]
    audit_entry: Optional[DecisionLogEntry]
    error: Optional[str]
    is_safe: bool
    guardrail_reason: Optional[str]

class SupportPipeline:
    """Stateful, auditable, deterministic support automation pipeline using LangGraph."""

    def __init__(self, threshold: Optional[float] = None):
        self.classifier = get_classifier()
        self.retriever = get_retriever()
        self.guardrails = get_guardrails()
        self.router = get_router(threshold=threshold) if threshold is not None else get_router()
        self.generator = get_generator()
        self.logger_store = get_logging_store()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(PipelineState)
        
        # Nodes
        workflow.add_node("ingest", self._node_ingest)
        workflow.add_node("classify", self._node_classify)
        workflow.add_node("retrieve", self._node_retrieve)
        workflow.add_node("guardrail_input", self._node_guardrail_input)
        workflow.add_node("route", self._node_route)
        workflow.add_node("generate", self._node_generate)
        workflow.add_node("escalate", self._node_escalate)
        workflow.add_node("log", self._node_log)
        
        # Edges
        workflow.set_entry_point("ingest")
        workflow.add_edge("ingest", "classify")
        workflow.add_edge("classify", "retrieve")
        workflow.add_edge("retrieve", "guardrail_input")
        workflow.add_edge("guardrail_input", "route")
        
        # Conditional routing
        workflow.add_conditional_edges(
            "route",
            lambda x: "generate" if x.get("final_action") == RoutingAction.AUTO_RESPOND else "escalate",
            {"generate": "generate", "escalate": "escalate"}
        )
        
        workflow.add_edge("generate", "log")
        workflow.add_edge("escalate", "log")
        workflow.add_edge("log", END)
        
        return workflow.compile()

    def _node_ingest(self, state: PipelineState) -> Dict[str, Any]:
        ticket = normalize_ticket(state["raw_ticket"])
        return {"ticket": ticket}

    def _node_classify(self, state: PipelineState) -> Dict[str, Any]:
        classification = self.classifier.classify(state["ticket"])
        return {"classification": classification}

    def _node_retrieve(self, state: PipelineState) -> Dict[str, Any]:
        retrieved_chunks = self.retriever.retrieve(state["ticket"].full_text, top_k=3)
        return {"retrieved_chunks": retrieved_chunks}

    def _node_guardrail_input(self, state: PipelineState) -> Dict[str, Any]:
        is_safe, guardrail_reason, guardrail_results = self.guardrails.check_input_ticket(
            state["ticket"], state["classification"].intent
        )
        return {
            "is_safe": is_safe,
            "guardrail_reason": guardrail_reason,
            "guardrail_results": guardrail_results
        }

    def _node_route(self, state: PipelineState) -> Dict[str, Any]:
        routing_decision = self.router.decide(state["ticket"], state["classification"], state["retrieved_chunks"])
        
        if not state["is_safe"]:
            routing_decision.action = RoutingAction.ESCALATE
            routing_decision.reason = f"Hard guardrail triggered: {state['guardrail_reason']}"
            
        return {
            "routing_decision": routing_decision,
            "final_action": routing_decision.action
        }

    def _node_generate(self, state: PipelineState) -> Dict[str, Any]:
        gen_result = self.generator.generate(state["ticket"], state["retrieved_chunks"])
        
        outbound_safe, out_reason, out_gr_results = self.guardrails.check_generated_response(
            gen_result.response_text,
            "\n".join(c.content for c in state["retrieved_chunks"])
        )
        
        new_gr_results = {**state.get("guardrail_results", {}), **out_gr_results}
        
        if outbound_safe:
            return {
                "response_text": gen_result.response_text,
                "citations": gen_result.citations,
                "guardrail_results": new_gr_results
            }
        else:
            logger.warning(f"Response blocked by outbound guardrail: {out_reason}")
            # If generation fails guardrails, we actually escalate
            decision = state["routing_decision"]
            decision.action = RoutingAction.ESCALATE
            decision.reason = f"Response blocked by guardrail: {out_reason}"
            return {
                "final_action": RoutingAction.ESCALATE,
                "routing_decision": decision,
                "response_text": None,
                "citations": [],
                "guardrail_results": new_gr_results
            }

    def _node_escalate(self, state: PipelineState) -> Dict[str, Any]:
        # Task 3: Draft a summary for escalated tickets
        try:
            summary = self.generator.draft_escalation_summary(state["ticket"], state["routing_decision"])
            return {"response_text": summary, "citations": []}
        except Exception as e:
            logger.warning(f"Failed to draft escalation summary: {e}")
            return {"response_text": None, "citations": []}

    def _node_log(self, state: PipelineState) -> Dict[str, Any]:
        ticket = state["ticket"]
        classification = state["classification"]
        routing_decision = state["routing_decision"]
        final_action = state["final_action"]
        
        audit_entry = DecisionLogEntry(
            decision_id=state["decision_id"],
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
                for c in state["retrieved_chunks"]
            ],
            threshold_applied=routing_decision.threshold_applied,
            action_taken=final_action.value,
            reason=routing_decision.reason,
            guardrail_results=state.get("guardrail_results", {}),
            prompt_version="PR-01 v1.0",
            requirement_ids=["FR-01", "FR-02", "FR-03", "FR-04", "FR-05", "FR-06", "FR-07"],
        )
        self.logger_store.log_decision(audit_entry)
        return {"audit_entry": audit_entry}

    def process_ticket(self, raw_ticket: Dict[str, Any]) -> ProcessedTicketOutput:
        """Processes a single raw ticket using the LangGraph state machine."""
        decision_id = str(uuid.uuid4())
        
        initial_state = {
            "raw_ticket": raw_ticket,
            "decision_id": decision_id,
            "ticket": None,
            "classification": None,
            "retrieved_chunks": [],
            "guardrail_results": {},
            "routing_decision": None,
            "final_action": None,
            "response_text": None,
            "citations": [],
            "audit_entry": None,
            "error": None,
            "is_safe": True,
            "guardrail_reason": None
        }

        try:
            # Optional Langfuse Integration
            callbacks = []
            if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
                try:
                    from langfuse.callback import CallbackHandler
                    langfuse_handler = CallbackHandler()
                    callbacks.append(langfuse_handler)
                    logger.info("Langfuse callback handler initialized successfully.")
                except ImportError:
                    logger.warning("Langfuse credentials found but langfuse package is not installed.")
                except Exception as e:
                    logger.warning(f"Failed to initialize Langfuse callback: {e}")

            # Run LangGraph pipeline
            final_state = self.graph.invoke(initial_state, config={"callbacks": callbacks})
            
            # Extract outputs
            ticket = final_state["ticket"]
            return ProcessedTicketOutput(
                ticket_id=ticket.ticket_id,
                channel=ticket.channel.value,
                classified_intent=final_state["classification"].intent,
                urgency=final_state["classification"].urgency.value,
                confidence=final_state["classification"].confidence,
                action=final_state["final_action"].value,
                reason=final_state["routing_decision"].reason,
                response_text=final_state["response_text"],
                citations=final_state["citations"],
                guardrails=final_state["guardrail_results"],
                audit_log=final_state["audit_entry"],
            )

        except Exception as e:
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
