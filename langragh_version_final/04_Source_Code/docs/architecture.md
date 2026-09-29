# CloudServe Intelligent Support System — Architectural Specification

## 1. Overview
The CloudServe Intelligent Support System is an auditable, deterministic support automation and escalation platform engineered to address failing support metrics at CloudServe Solutions. Rather than operating as an ungrounded conversational chatbot, the system functions as a strictly gated decision pipeline.

```
                    ┌───────────────────────────────┐
                    │    Multi-Channel Ingestion    │  (Email, Chat, Docs, Forum)
                    │         (src/ingest.py)       │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Calibrated Classification   │  (22 Intents, Urgency, Conf)
                    │        (src/classify.py)      │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
       ┌─────────────────────────┐     ┌─────────────────────────┐
       │   Semantic Retrieval    │     │    Input Guardrails     │
       │    (src/retrieve.py)    │     │   (src/guardrails.py)   │
       │  (145 passage chunks)   │     │ (PII, Injections, Redl) │
       └────────────┬────────────┘     └────────────┬────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │  Deterministic Routing Engine │  (Confidence threshold tau,
                    │         (src/route.py)        │   Safety Gate, KB gate)
                    └───────┬───────────────┬───────┘
                            │               │
            Action: 'escalate'      Action: 'auto_respond'
                            │               │
                            │               ▼
                            │  ┌─────────────────────────┐
                            │  │   Grounded Generation   │ (Citations [DOC-XXX],
                            │  │    (src/generate.py)    │  Zero hallucinations)
                            │  └────────────┬────────────┘
                            │               │
                            │               ▼
                            │  ┌─────────────────────────┐
                            │  │   Outbound Guardrails   │ (Prohibited claims,
                            │  │   (src/guardrails.py)   │  Grounding validation)
                            │  └────────────┬────────────┘
                            │               │
                            │         Pass / Fail
                            │          (If Fail -> escalate)
                            │               │
                            ▼               ▼
                    ┌───────────────────────────────┐
                    │     1:1 Decision Audit Log    │  (SQLite & JSONL store,
                    │    (src/logging_store.py)     │   Governance schema)
                    └───────────────────────────────┘
```

## 2. Key Components
1. **Multi-Channel Ingestion (`src/ingest.py`)**: Normalizes disparate payload schemas into a unified Pydantic v2 `NormalizedTicket`.
2. **Calibrated Classifier (`src/classify.py`)**: Predicts across 22 canonical intents and assigns urgency, recording alternative candidates and calibrated probability confidence $\in [0, 1]$.
3. **Passage Retrieval (`src/retrieve.py`)**: Chunks the 29 documentation articles into 145 discrete section chunks with persistent chunk IDs (`DOC-XXX#sec-Y`) and conducts hybrid semantic retrieval.
4. **Deterministic Routing Engine (`src/route.py`)**: Enforces an empirical confidence threshold ($\tau = 0.55$) and hard safety gates (`must_not_auto_respond`). Identical inputs produce identical routing decisions.
5. **Grounded Generation (`src/generate.py`)**: Constructs factual answers citing retrieved chunk IDs, backed by an extractive fallback when LLM providers are unavailable.
6. **Hard Guardrails (`src/guardrails.py`)**: Evaluates inbound tickets and outbound responses for PII, prompt injections, and prohibited claims (e.g., refund promises).
7. **Audit Logging Store (`src/logging_store.py`)**: Maintains a strict 1:1 persistent audit trail across SQLite and JSONL formats matching the Governance Framework specification.
