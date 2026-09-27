# CloudServe Intelligent Support System (FDE Capstone)

An auditable, deterministic support automation and escalation platform engineered for CloudServe Solutions.

## System Overview
The system implements a stateful, auditable pipeline that normalizes multi-channel support tickets (Email, Chat, Docs Comments, Forum), performs calibrated intent & urgency classification, searches authoritative documentation, enforces safety redlines via hard guardrails, drafts grounded answers with citations, and writes every decision to a 1:1 persistent audit trail.

---

## Quickstart & Installation (A1: Clean Checkout)

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.11 and 3.12)
- Git

### 2. Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Note: System operates with 100% offline determinism and resilience even without an external API key).*

---

## Running the System

### 1. Execute The Gate (Unattended Evaluation Harness — A9 & A10)
Run the automated evaluation harness unattended on any input ticket dataset:
```bash
python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/
```
This produces:
- `evaluation/results/evaluation_report.md` (Markdown summary report)
- `evaluation/results/evaluation_metrics.json` (Structured metric payloads)
- `evaluation/results/processed_tickets.json` (Output ticket predictions & citations)
- `evaluation/results/decisions_eval.db` (Persistent SQLite decision audit store)
- `evaluation/results/decisions_eval.jsonl` (JSONL audit log)

### 2. Run the Test Suite (A12: Pass-First Test Suite)
Execute the complete `pytest` test suite:
```bash
python -m pytest tests/ -v
```

### 3. Start the FastAPI Service
Launch the REST API server:
```bash
python -m src.api
```
The interactive Swagger API documentation is available at `http://localhost:8000/docs`.

---

## Acceptance Criteria Verification (A1 – A12)

- **A1: Clean Checkout**: Verified by standard virtualenv creation and package installation commands.
- **A2: Multi-Channel Ingestion**: Handles Email, Chat, Docs Comments, and Forum into unified `NormalizedTicket` schema (`src/ingest.py`).
- **A3: Calibrated Classification**: 22 intents + Urgency with calibrated confidence $\in [0, 1]$ (`src/classify.py`).
- **A4: Semantic Passage Retrieval**: Chunks 29 KB articles into 145 sections with real chunk IDs (`src/retrieve.py`).
- **A5: Deterministic Routing Engine**: Empirical threshold ($\tau = 0.55$) + safety gates. Identical inputs yield identical decisions (`src/route.py`).
- **A6: Grounded Generation**: Cites verified chunk IDs (e.g., `[DOC-AUTH-004#sec-1]`) with zero ungrounded promises (`src/generate.py`).
- **A7: Hard Guardrails**: Blocks responses and escalates on PII, prohibited claims, toxic tone, or prompt injection (`src/guardrails.py`).
- **A8: 1:1 Decision Audit Trail**: Every processed ticket generates an audit log entry in SQLite and JSONL matching the Governance Framework schema (`src/logging_store.py`).
- **A9: The Gate (Unattended Run)**: CLI accepts `--input` and `--output` flags and evaluates unattended without crashing (`evaluation/harness.py`).
- **A10: Automated Metrics Report**: Generates markdown and JSON metrics reports automatically post-evaluation (`evaluation/results/`).
- **A11: Resilient Fault Tolerance**: Graceful degradation on timeouts, disconnects, and malformed inputs (`src/pipeline.py`).
- **A12: Pass-First Test Suite**: Comprehensive tests passing via `python -m pytest tests/ -v`.
