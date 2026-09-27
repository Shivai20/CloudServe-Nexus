# Stage 2: Product Requirements Document (PRD v1.0)

## What We Did
In this stage, we transitioned from the raw data and insights discovered in Stage 1 to formalizing the product requirements. We filled out the `Stage_2_PRD_Template.docx` with concrete, testable requirements that align directly with the acceptance criteria (A1-A12) of the FDE Capstone.

## How We Did It
We wrote a Python automation script (`scripts/populate_stage2.py`) using the `python-docx` library to programmatically edit the Word document, similar to our approach in Stage 1. 

Here is a breakdown of the key sections we populated:

### 1. Problem Statement
We framed the problem mathematically using our Stage 1 baseline metrics: 
*   High resolution times (**7.0 hours avg**) and inconsistent CSAT (**2.97/5.0**).
*   **71.4%** of tickets are highly repetitive and already answered in documentation.
*   **17.4%** are sensitive ("must_not_auto_respond") and need immediate escalation.
*   Language equity is poor (non-fluent English tickets take **58 minutes longer**).
*   **Goal:** A deterministic AI routing and response system.

### 2. User Personas & Job-to-be-Done (JTBD)
We defined our core users to ensure the PRD remains grounded in actual needs:
*   **Customers:** Need fast, accurate answers. Success = higher CSAT and reduced wait times.
*   **Tier 1 Agents:** Need to stop answering repetitive (71.4%) tickets. Success = reduced manual ticket volume.
*   **Tier 2/Specialist Agents:** Need sensitive (17.4%) tickets routed to them immediately without AI interference. Success = 100% of redline issues routed successfully.
*   **Head of Support:** Needs auditable metrics. Success = 1:1 decision log generation (Requirement A8).

### 3. Functional Requirements (FR-01 to FR-12)
These are the core capabilities the system *must* have. Each one is tied to empirical evidence and a specific testable outcome:
*   **Ingestion (FR-01):** Handle Email, Chat, Docs Comments, and Forum.
*   **Classification & Routing (FR-02, FR-04):** Classify 22 intents + Urgency and route based on a strict confidence threshold.
*   **Retrieval & Generation (FR-03, FR-05):** Pull from the 29 KB articles and generate responses *only* based on retrieved text (no hallucinations).
*   **Guardrails (FR-06):** Stop any PII, hallucination, or toxic tone.
*   **Auditability & CLI (FR-07, FR-08, FR-10):** Must have a 1:1 decision log, run unattended via CLI, and output an evaluation report.
*   **Language Equity (FR-11):** Must not penalize non-fluent English users.
*   **Testing (FR-12):** Pass-first `pytest` suite.

### 4. Non-Functional Requirements & Metrics
We established requirements around Latency, Availability, Accuracy, Privacy, Auditability, and Maintainability. 
We set target metrics based on our baseline:
*   **First Contact Resolution (FCR):** Target >= 60% (up from 43.8%).
*   **Time to first reply:** Target < 5 minutes (down from 8-12 hours).
*   **CSAT:** Target >= 4.0 (up from 2.97).
*   **Escalation Rate:** Target <= 40% (down from 56.2%).

## Why This Matters
By rooting the PRD entirely in the Stage 1 data, we ensure that we are building the *right* thing—a verifiable, enterprise-grade AI pipeline—rather than a generic, untestable "chatbot." The metrics and requirements set here will act as our grading rubric in Stage 5 (Evaluation).
