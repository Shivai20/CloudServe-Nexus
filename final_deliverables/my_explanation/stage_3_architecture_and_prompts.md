# Stage 3: System Architecture & Prompt Library

## What We Did
In this stage, we translated the Functional Requirements (FRs) from the PRD into concrete technical specifications and engineered the precise LLM prompts needed to power the intelligence of the system. We populated the `Stage_3_Prompt_Library.docx`.

## How We Did It
We wrote another Python automation script (`scripts/populate_stage3.py`) to systematically inject our architecture designs and prompts into the Word document.

### 1. Requirements to Specifications Mapping
We mapped every single Functional Requirement (FR-01 to FR-12) to a specific system component, defining its precise Inputs, Outputs, and Acceptance Criteria.
*   **Example (FR-04: Routing):** Input = Confidence Score & Safety Flag. Output = Action (Respond or Escalate). Criteria = Identical inputs yield identical outputs.
*   **Example (FR-07: Audit):** Input = Ticket ID & Routing Action. Output = Audit Log JSON. Criteria = 1:1 reconciliation with the input dataset.

### 2. Prompt Engineering (The "Brain" of the System)
We defined the three core prompts that act as nodes in our deterministic pipeline. Because we require deterministic, structured outputs for our pipeline to function, all prompts enforce strict JSON output schemas.

*   **Prompt 1: Intent Classification (Serves FR-02)**
    *   *Purpose:* Classify the ticket into one of the 22 intents and assign an urgency score.
    *   *Mechanism:* Outputs a JSON containing `intent`, `confidence` (float), and `urgency`.
*   **Prompt 2: Safety Guardrails (Serves FR-06)**
    *   *Purpose:* Act as a hard gatekeeper for the `must_not_auto_respond` redlines (PII, security, billing).
    *   *Mechanism:* Outputs a JSON containing an `is_safe` boolean and a `reason` if unsafe. If `is_safe` is false, the system immediately escalates, bypassing generation.
*   **Prompt 3: Grounded Generation (Serves FR-05)**
    *   *Purpose:* Draft the response sent to the user.
    *   *Mechanism:* Strictly constrained to ONLY use facts from provided `<CHUNKS>`. Outputs a JSON containing the `answer` and an array of `citations` (chunk IDs).

### 3. Traceability Matrix
We populated the traceability matrix (Table 11) to prove that every single requirement has a corresponding specification, is covered by a prompt (or pure code logic), and has a dedicated test case (e.g., `test_classification_accuracy`, `test_guardrails_escalation`).

## Why This Matters
By strictly defining the inputs and outputs (JSON schemas) for every prompt, we transform unpredictable LLM generations into deterministic software functions. This is how we guarantee the system will meet the strict A1-A12 acceptance criteria, especially the 1:1 Auditability (A8) and Safety Guardrails (A7). The pipeline architecture is now fully planned and ready to be built.
