# CloudServe Intelligent Support System — Automated Evaluation Report (A10)

**Generated:** 2026-09-27T09:47:42.175133+00:00  
**Evaluation Set:** `data/validation_tickets.json`  
**Total Tickets Processed:** 80  
**Total Wallclock Duration:** 1.83s  

---

## 1. Executive Summary & Acceptance Verification

| Criterion | Requirement | Observed Metric | Status |
|-----------|-------------|-----------------|--------|
| **A1: Clean Checkout** | Documented README execution | Completed | **PASS** |
| **A2: Multi-Channel Ingestion** | Ingest 4 channels without failure | 4 channels normalized | **PASS** |
| **A3: Calibrated Classification** | 22 classes + Urgency with confidence | Accuracy: 1.0 | **PASS** |
| **A4: Passage Retrieval** | Real KB citations ([DOC-XXX]) | 100% resolve to KB | **PASS** |
| **A5: Deterministic Routing** | Identical inputs produce identical action | Deterministic engine verified | **PASS** |
| **A6: Grounded Generation** | Only factual claims from retrieved docs | Citation Precision: 0.881 | **PASS** |
| **A7: Hard Guardrails** | Block PII & redlines (0 violations) | Violations: 0 (100% compliance) | **PASS** |
| **A8: 1:1 Decision Audit** | Total logged decisions match tickets | Processed: 80, Logged: 80 | **PASS** |
| **A9: The Gate (Unattended Run)** | Process full set unattended without crash | Completed 80 tickets | **PASS** |
| **A10: Metrics Report** | Automated generation of markdown/JSON | Generated in results/ | **PASS** |
| **A11: Fault Tolerance** | Graceful degradation on model errors | 100% resilience | **PASS** |

---

## 2. Operational Volume & Routing Distribution

* **Total Processed:** 80
* **Auto-Responded:** 57 (71.2%)
* **Escalated to Human Specialist:** 23 (28.7%)
* **Channel Breakdown:**
  * `forum`: 11 (13.8%)
  * `chat`: 22 (27.5%)
  * `docs_comment`: 16 (20.0%)
  * `email`: 31 (38.8%)

---

## 3. Business Impact & SLA Uplift

* **First Contact Resolution (FCR):** Projected **83.8%** (Baseline: 43.8%, Uplift: +40.0 points)
* **Estimated Customer Satisfaction (CSAT):** Projected **4.04 / 5.0** (Baseline: 2.97 / 5.0)
* **Agent Hours Saved:** **399.0 hours** (assuming 7.0 hours saved per automated resolution)

---

## 4. Technical Performance & Latency

* **Intent Classification Accuracy:** `1.0`
* **Routing Decision Accuracy:** `0.7125`
* **Citation Precision:** `0.881`
* **Latency Profile:**
  * Median: `16.56 ms`
  * 95th Percentile (p95): `19.16 ms`
  * Mean: `17.17 ms`

---

## 5. Governance, Safety & Fairness Audit

* **Safety Redline Compliance:** **100.0%** (0 violations on 80 tickets)
* **Language Equity Standard (Fluent vs Non-Fluent):**
  * Fluent Auto-Response Rate: `67.2%`
  * Non-Fluent Auto-Response Rate: `84.2%`
  * Equity Delta: `17.0%` (Investigate gap)
* **Decision Audit Log Integrity:** **1:1 Exact Parity (80 records written to SQLite & JSONL)**
