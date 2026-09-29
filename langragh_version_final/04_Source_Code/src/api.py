"""FastAPI Application for CloudServe Support System.

Exposes REST endpoints for real-time ticket ingestion, batch processing,
decision audit log querying, and operational metrics.
Executable via: python -m src.api
"""

from typing import Any, Dict, List, Optional
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram
from pydantic import BaseModel
import time
from src.logging_store import get_logging_store
from src.models import DecisionLogEntry, ProcessedTicketOutput
from src.pipeline import SupportPipeline

app = FastAPI(
    title="CloudServe Intelligent Support API",
    version="1.0.0",
    description="Deterministic, auditable support automation and routing engine.",
)

# Prometheus Metrics
TICKETS_PROCESSED = Counter("cloudserve_tickets_processed_total", "Total tickets processed")
TICKETS_ESCALATED = Counter("cloudserve_tickets_escalated_total", "Total tickets escalated")
TICKETS_AUTORESPONDED = Counter("cloudserve_tickets_autoresponded_total", "Total tickets auto-responded")
PIPELINE_LATENCY = Histogram("cloudserve_pipeline_latency_seconds", "Pipeline processing time")

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = SupportPipeline()
store = get_logging_store()

class HealthResponse(BaseModel):
    status: str
    version: str
    pipeline_ready: bool
    total_decisions_logged: int


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint confirming service and database availability."""
    decisions = store.get_all_decisions()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        pipeline_ready=True,
        total_decisions_logged=len(decisions),
    )


@app.post("/tickets", response_model=ProcessedTicketOutput, status_code=status.HTTP_200_OK)
def process_ticket(ticket: Dict[str, Any]):
    """Process a single incoming ticket through the complete support pipeline."""
    TICKETS_PROCESSED.inc()
    start_time = time.time()
    try:
        result = pipeline.process_ticket(ticket)
        if result.action == "auto_respond":
            TICKETS_AUTORESPONDED.inc()
        else:
            TICKETS_ESCALATED.inc()
        PIPELINE_LATENCY.observe(time.time() - start_time)
        return result
    except Exception as e:
        TICKETS_ESCALATED.inc()
        raise HTTPException(status_code=500, detail=f"Pipeline processing error: {str(e)}")


@app.post("/tickets/batch", response_model=List[ProcessedTicketOutput])
def process_tickets_batch(tickets: List[Dict[str, Any]]):
    """Process a batch of tickets, maintaining 1:1 audit log reconciliation."""
    return pipeline.process_batch(tickets)


@app.get("/decisions", response_model=List[Dict[str, Any]])
def list_decisions(limit: int = Query(100, ge=1, le=1000)):
    """Query recent logged decision records from the audit database."""
    decisions = store.get_all_decisions()
    return decisions[-limit:]


@app.get("/stats")
def get_metrics():
    """Operational metrics covering volume, escalation rate, and guardrail stats."""
    decisions = store.get_all_decisions()
    total = len(decisions)
    if total == 0:
        return {
            "total_processed": 0,
            "auto_respond_rate": 0.0,
            "escalation_rate": 0.0,
            "guardrail_blocks": 0,
        }

    auto_count = sum(1 for d in decisions if d.get("action_taken") == "auto_respond")
    esc_count = sum(1 for d in decisions if d.get("action_taken") == "escalate")
    block_count = sum(1 for d in decisions if d.get("action_taken") == "block")

    return {
        "total_processed": total,
        "auto_respond_count": auto_count,
        "escalation_count": esc_count,
        "auto_respond_rate": round(auto_count / total, 4),
        "escalation_rate": round(esc_count / total, 4),
        "guardrail_blocks": block_count,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
