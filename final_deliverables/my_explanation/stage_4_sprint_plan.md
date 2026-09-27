# Stage 4: Sprint Plan

## What We Did
In this stage, we converted our Product Requirements (Stage 2) and System Architecture (Stage 3) into an actionable, prioritized backlog and scheduled the work across a two-week sprint. We populated the `Stage_4_Sprint_Plan.docx`.

## How We Did It
Using our Python script (`scripts/populate_stage4.py`), we broke down the engineering effort into 12 discrete backlog items (`B-01` through `B-12`).

### 1. The Backlog (B-01 to B-12)
We created a strict dependency chain to ensure we don't build things out of order. Every item has a specific "Definition of Done" tied to our A1-A12 acceptance criteria.
*   **Data & Infrastructure (B-01 to B-04):** Environment setup, normalizing the 500 tickets, and chunking/embedding the 29 KB articles. (Must happen first).
*   **The LLM Nodes (B-05, B-06, B-08):** Building the Python code that wraps our three core prompts (Classification, Guardrails, Generation) to enforce structured JSON outputs.
*   **The Logic Engine (B-07, B-09):** The deterministic routing engine that glues the nodes together and handles network faults gracefully.
*   **Evaluation & Logging (B-10 to B-12):** Generating the 1:1 audit log and the CLI testing interface to run the evaluation unattended.

### 2. Sprint Schedule
We scheduled the work logically:
*   **Week 1:** Focuses purely on data ingestion, retrieval, and getting the individual LLM nodes functioning and parsing JSON correctly.
*   **Week 2:** Focuses on pipeline integration, fault tolerance, generating the strict audit logs, and writing the final `pytest` test suite.

### 3. Scope Cutting Strategy
As a Senior FDE, it is crucial to know what to drop if time runs out, without violating the core A1-A12 criteria. We defined our scope cuts:
1.  *Complex query re-writing:* We will drop this first. It might slightly lower retrieval accuracy, but the core pipeline will still function.
2.  *Multi-threading the CLI:* We will process tickets sequentially if concurrency proves too difficult to stabilize. Latency will suffer, but accuracy and auditability will remain intact.

## Why This Matters
Planning the sprint dependencies prevents us from writing "spaghetti code." By the time we start building the Generation node, we already know the Retrieval node works. Furthermore, knowing exactly what to cut ensures we don't compromise the mandatory A7 (Guardrails) and A8 (Auditability) requirements just to ship a "fancy" feature.

We are now ready for **Stage 5: The Build**. As per your preference, we will switch to **Gemini Flash** for this phase to maximize coding throughput and speed.
