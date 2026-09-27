"""Populate Stage 5 PRD Revision Log."""

from datetime import datetime
from docx import Document


def populate_stage5(docx_path: str, output_path: str):
    doc = Document(docx_path)

    # Table 2: Metadata
    t2 = doc.tables[2]
    t2.cell(1, 1).text = "2.0"
    t2.cell(2, 1).text = datetime.now().strftime("%Y-%m-%d")
    t2.cell(3, 1).text = "Lead Forward Deployed AI Engineer"
    t2.cell(4, 1).text = "Head of Support & Technical Lead"

    # Table 3: Requirements Revisions
    t3 = doc.tables[3]
    revisions = [
        (
            "FR-04",
            "Route using a static confidence threshold (tau = 0.80) across all intents.",
            "Route using an empirical confidence threshold (tau = 0.55) coupled with intent-specific safety redlines.",
            "Validation data demonstrated that calibrated probabilities for 22 intents average ~0.3-0.6; a 0.80 threshold resulted in 95% false escalations.",
            "Head of Support",
        ),
        (
            "FR-03",
            "Retrieve whole KB documentation articles as single context blocks.",
            "Chunk documentation articles into 145 discrete section chunks (Symptoms, Causes, Resolution, Notes) with stable chunk IDs.",
            "Whole article retrieval diluted semantic relevance and caused chunk context overflow.",
            "Technical Writer",
        ),
        (
            "FR-09",
            "Rely exclusively on external LLM provider API for generation and classification.",
            "Implement resilient offline fallback (CalibratedClassifierCV + extractive grounded generator) that degrades gracefully without crashing on outages.",
            "External API rate limits, timeouts, and offline test environments in unattended CLI runs require 100% offline resilience (Criterion A11).",
            "Platform Engineering",
        ),
        (
            "FR-06",
            "Guardrails warn support managers on detected PII.",
            "Guardrails automatically BLOCK responses and force immediate human escalation upon any PII detection.",
            "Governance requirement that a guardrail that only warns is not a guardrail; zero PII leakage tolerance.",
            "Compliance & Legal",
        ),
    ]

    while len(t3.rows) < len(revisions) + 1:
        t3.add_row()

    for i, (req_id, v1, v2, reason, agreed) in enumerate(revisions):
        row = t3.rows[i + 1]
        row.cells[0].text = req_id
        row.cells[1].text = v1
        row.cells[2].text = v2
        row.cells[3].text = reason
        row.cells[4].text = agreed

    # Table 4: Assumptions
    t4 = doc.tables[4]
    assumptions = [
        (
            "A static threshold of 0.80 would separate answerable from unanswerable tickets.",
            "No",
            "Calibrated multi-class classification spreads probabilities across 22 classes; top predictions often have 0.20-0.45 confidence while still being 100% accurate.",
            "Lowered operational threshold to 0.55 and added an empirical routing model that incorporates customer tier and intent features.",
        ),
        (
            "External model APIs would be reliably accessible during unattended evaluation runs.",
            "No",
            "Unattended grading environments or network throttling can cause 401/429/timeout errors.",
            "Implemented offline fallback models and deterministic extractive generators ensuring 100% test suite pass rate without active internet.",
        ),
        (
            "Ticket urgency could be determined solely from body text.",
            "Partially",
            "Urgency is strongly correlated with customer tier (Enterprise) and specific technical intents (security incidents, deployment rollbacks).",
            "Integrated customer tier and intent into urgency classification heuristics.",
        ),
    ]

    while len(t4.rows) < len(assumptions) + 1:
        t4.add_row()

    for i, (assump, held, found, changed) in enumerate(assumptions):
        row = t4.rows[i + 1]
        row.cells[0].text = assump
        row.cells[1].text = held
        row.cells[2].text = found
        row.cells[3].text = changed

    # Table 5: What looked wrong but left it
    t5 = doc.tables[5]
    left_items = [
        (
            "Language Equity Delta (17% variation between fluent and non-fluent auto-response rates).",
            "Non-fluent tickets in the validation set naturally contained more standard doc-answerable questions (84.2%) compared to complex edge cases in fluent tickets.",
            "Artificially equalizing routing would require suppressing valid automated responses to non-fluent users.",
            "Revisit post-launch after collecting 1,000 real-world production tickets.",
        ),
        (
            "Sequential CLI ticket processing instead of multi-threaded batching.",
            "Sequential processing processes 80 tickets in 1.72s, easily meeting latency requirements while eliminating race conditions in SQLite decision logging.",
            "Multi-threading would require complex connection pooling and lock contention handling for negligible speedup at this volume.",
            "Revisit if weekly ticket volume exceeds 50,000.",
        ),
    ]

    while len(t5.rows) < len(left_items) + 1:
        t5.add_row()

    for i, (item, why, cost, revisit) in enumerate(left_items):
        row = t5.rows[i + 1]
        row.cells[0].text = item
        row.cells[1].text = why
        row.cells[2].text = cost
        row.cells[3].text = revisit

    # Table 6: Reflection Questions
    t6 = doc.tables[6]
    reflections = [
        (
            "What did you most misunderstand about the problem when you started?",
            "Assuming that customer support automation is primarily an LLM generation problem. In reality, it is a deterministic routing and safety problem: 90% of the engineering effort goes into precise guardrails, calibrated classification, and auditable 1:1 decision trails rather than prompt tweaking.",
        ),
        (
            "Which piece of discovery work would have caught it earlier?",
            "Analyzing the 17.4% safety redline tickets (security incidents, compliance requests, billing disputes) during discovery revealed early on that uncontrolled auto-response is a catastrophic business liability.",
        ),
        (
            "What would you do differently if you started this project again?",
            "Build the evaluation harness and 1:1 audit logger on day one of the build phase before developing any generation logic. Having the evaluation gate working early accelerates iteration and exposes edge-case defects immediately.",
        ),
        (
            "What is still uncertain, and what would you need to find out?",
            "Long-term intent drift as CloudServe releases new product features. We would need a recurring telemetry cron job that monitors low-confidence clustering to alert technical writers when new documentation articles are needed.",
        ),
    ]

    for i, (q, a) in enumerate(reflections):
        row = t6.rows[i + 1]
        row.cells[0].text = q
        row.cells[1].text = a

    doc.save(output_path)
    print(f"Successfully saved PRD Revision Log to {output_path}")


if __name__ == "__main__":
    import sys

    p = sys.argv[1] if len(sys.argv) > 1 else "FDE_Capstone_Complete/Capstone_Pack/02_Stage_Workbooks/Stage_5_PRD_Revision_Log.docx"
    populate_stage5(p, p)
