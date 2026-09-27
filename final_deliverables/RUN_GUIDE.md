# 🚀 Run & Test Guide: CloudServe Intelligent Support System

This guide covers the three main ways to run, test, and interact with the system we've built. 

Ensure you are in the project root directory: `FDE_Capstone_Complete-20260821T084330Z-1-001` and your Python environment is activated.

---

## 1. Run the Test Suite (Pytest)
This runs our comprehensive test suite, verifying that all individual components (Ingestion, Classification, Retrieval, Guardrails, Routing, Generation) are working correctly and the pipeline handles edge cases.

**Command:**
```powershell
python -m pytest tests/ -v
```

**What to look for:**
- You should see 9 passing tests.
- This verifies Acceptance Criterion A12 (Pass-First Test Suite).

---

## 2. Run the Evaluation Harness (Unattended CLI)
This runs the full system across the 80-ticket validation dataset (`data/validation_set.jsonl`). It tests the end-to-end deterministic pipeline, generates the metrics report, and populates the audit log.

**Command:**
```powershell
python evaluation/harness.py --input data/validation_tickets.json --output evaluation/results/
```

**What to look for:**
- The script will process all 80 tickets without human intervention.
- It will output a markdown report: `evaluation/metrics_report.md`.
- It will generate a strict 1:1 decision audit trail: `storage/logs.jsonl`.
- This verifies Acceptance Criteria A8 (1:1 Audit Trail), A9 (The Gate), and A10 (Automated Metrics Report).

---

## 3. Run the Live API Server (FastAPI)
This starts the live REST API, which is how a real front-end or customer portal would interact with the CloudServe Support System.

**Command:**
```powershell
uvicorn src.api:app --reload
```
*(The server will start at `http://127.0.0.1:8000`)*

**How to interact with it:**

1. **Swagger UI (Interactive Docs):** 
   Open your browser and navigate to: `http://127.0.0.1:8000/docs`. Here you can easily construct JSON payloads and test the `/tickets` endpoint manually.

2. **PowerShell Tests:**
   With the server running in one terminal, open a new terminal and try these different test payloads:

   *Test Payload 1: Standard Auto-Response (Password Reset)*
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/tickets" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"ticket_id": "TEST-001", "channel": "Email", "subject": "Forgot password", "body": "How do I reset my account password?", "customer_tier": "Standard"}'
   ```

   *Test Payload 2: Guardrail Triggered (PII Leak -> Escalate)*
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/tickets" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"ticket_id": "TEST-002", "channel": "Chat", "subject": "Delete my account", "body": "Hi, I want to close my account. My social security number is 123-456-7890.", "customer_tier": "Premium"}'
   ```

   *Test Payload 3: Guardrail Triggered (Billing Redline -> Escalate)*
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/tickets" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"ticket_id": "TEST-003", "channel": "Email", "subject": "Billing issue", "body": "You overcharged me by $500 last month. I want a refund now.", "customer_tier": "Enterprise"}'
   ```

   **Expected Response:** The system will process each and return a JSON payload indicating the decision (`action` will be either `"auto_respond"`, `"escalate"`, or `"block"`).
