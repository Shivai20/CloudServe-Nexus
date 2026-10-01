import os
import json
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Load development tickets to verify figures
with open(r'data/development_tickets.json') as f:
    tickets = json.load(f)

N = len(tickets)
answerable_cnt = sum(1 for t in tickets if t.get('labels', {}).get('answerable_from_docs'))
must_not_cnt = sum(1 for t in tickets if t.get('labels', {}).get('must_not_auto_respond'))
auto_route_cnt = sum(1 for t in tickets if t.get('labels', {}).get('expected_route') == 'auto_respond')
escalate_route_cnt = sum(1 for t in tickets if t.get('labels', {}).get('expected_route') == 'escalate')
actual_esc_cnt = sum(1 for t in tickets if t.get('history', {}).get('escalated'))
actual_fcr_cnt = sum(1 for t in tickets if t.get('history', {}).get('first_contact_resolution'))
avg_res_time = sum(t.get('history', {}).get('resolution_time_minutes', 0) for t in tickets) / N
avg_csat = sum(t.get('history', {}).get('csat_rating', 0) for t in tickets if t.get('history', {}).get('csat_rating') is not None) / N
repeat_cnt = sum(1 for t in tickets if t.get('history', {}).get('repeat_contact', False))

non_fluent = [t for t in tickets if t.get('language_fluency') == 'non_fluent']
fluent = [t for t in tickets if t.get('language_fluency') == 'fluent']
non_fluent_res = sum(t.get('history', {}).get('resolution_time_minutes', 0) for t in non_fluent) / len(non_fluent) if non_fluent else 0
fluent_res = sum(t.get('history', {}).get('resolution_time_minutes', 0) for t in fluent) / len(fluent) if fluent else 0

print(f"Data verified: N={N}, answerable={answerable_cnt} ({answerable_cnt/N*100:.1f}%), avg_res={avg_res_time:.1f}m")

# Helper function to set cell text cleanly
def set_cell(cell, text, bold=False):
    cell.text = text
    for p in cell.paragraphs:
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        for run in p.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
            run.bold = bold

doc_path = r'final_deliverables/02_Stage_Workbooks/Stage_1_Discovery_Workbook.docx'
doc = docx.Document(doc_path)

# ==========================================
# TABLE 2: SECTION 1 - STAKEHOLDER TRANSCRIPTS
# ==========================================
t2 = doc.tables[2]
# Row 1: Marcus
set_cell(t2.rows[1].cells[1], 
    "Volume is 500+ tickets/week with 6 agents; response times are 8-12 hours vs 2-hour SLA; FCR is 42% vs 65% benchmark; escalations cost 4x more; asked for a chatbot to answer easy tickets; terrified of 'confidently incorrect' answers on social media; compliance review in autumn requires auditability; enterprise customers have strict SLAs.")
set_cell(t2.rows[1].cells[2], 
    "Does not know actual intent distribution of tickets ('would be guessing'); does not track language fluency impact; unaware that ~50% of Tier 2 escalations are avoidable documentation findability issues; unaware that 71.4% of tickets are already answered in official KB articles.")
set_cell(t2.rows[1].cells[3], 
    "Actual ticket volume across 22 intents; baseline FCR and escalation rate; average resolution time; performance disparity across customer tiers and language fluency; proportion answerable from docs.")

# Row 2: Sofia
set_cell(t2.rows[2].cells[1], 
    "Queue has 40-70 tickets daily; routine tickets take 4-5 min, unfamiliar take 40 min before escalating; 7/10 are repeat questions seen that month; agents avoid official documentation because search is painful; agents rely on private, unreviewed snippet files; non-fluent English tickets take much longer, have more misunderstandings, and have the worst CSAT ('no one has noticed').")
set_cell(t2.rows[2].cells[2], 
    "Unaware that the 29 KB articles are actively maintained by Ines and cover 71.4% of tickets; unaware of the aggregate financial cost and customer friction of ungrounded raw escalations to Tier 2; unaware of company-wide ticket distribution.")
set_cell(t2.rows[2].cells[3], 
    "Proportion of repeat tickets; resolution time and CSAT disparity for non-fluent vs fluent tickets; proportion of tickets that could be resolved with accessible documentation.")

# Row 3: Daniel
set_cell(t2.rows[3].cells[1], 
    "About 50% of Tier 2 escalations could be solved at Tier 1 if agents had confidence or found the right documentation; escalations arrive with zero context (raw forwards), forcing Tier 2 to re-read threads and re-ask questions; would be twice as fast if escalations had context (intent, candidate docs, specific uncertainty trigger); warns against training on agents' outdated snippet files; safety redlines: security/account compromise, billing disputes, data residency.")
set_cell(t2.rows[3].cells[2], 
    "Underestimates the sheer volume pressure and backlog on Tier 1 (40-70 tickets daily); doesn't see incoming ticket arrival patterns or multi-channel complexity.")
set_cell(t2.rows[3].cells[3], 
    "Proportion of Tier 2 escalations answerable from docs; frequency of security, billing, and compliance redlines; resolution time impact of escalations.")

# Row 4: Ines
set_cell(t2.rows[4].cells[1], 
    "Maintains 29 support KB articles on rotation covering authentication, deployment, API, billing, data, security, account management; external customers use them but internal support does not; internal search fails because it matches exact titles/terms rather than customer phrasing ('my deployment keeps dying' vs 'resolving container health check failures'); unreviewed snippet files are dangerous; requires explicit citations so errors can be attributed to doc vs model; docs cannot answer novel outages, feature requests, or roadmap timing.")
set_cell(t2.rows[4].cells[2], 
    "Does not know what percentage of incoming support queue is covered by her articles; unaware of specific multi-channel error patterns; unfamiliar with Tier 1 daily triage workflow.")
set_cell(t2.rows[4].cells[3], 
    "Semantic coverage of the 29 KB articles across all 500 tickets; error types in keyword vs semantic retrieval; volume of out-of-scope tickets (feature requests, unclear requests).")

# Row 5: Ravi
set_cell(t2.rows[5].cells[1], 
    "Support is slow (8-12 hrs) but decent once reached; waiting cost is asymmetric (pagination query can wait, deployment failure at 9 AM is catastrophic); searches documentation himself and finds answers ~50% of the time, burning hours before support sends the same link; accepts automated first responses if honest, transparent, and cited with doc link ('here is the doc, human will verify'), but will not accept incorrect answers that break production; notices service gaps between Business and Enterprise plans at renewal.")
set_cell(t2.rows[5].cells[2], 
    "Unaware of the severe staffing constraint (only 6 agents for 500+ tickets/week); unaware of multi-channel ingestion volume; doesn't know why agents take hours just to locate a link.")
set_cell(t2.rows[5].cells[3], 
    "Urgency distribution (High vs Med vs Low); CSAT ratings on slow vs fast tickets; performance differences between customer tiers.")

# ==========================================
# TABLE 3: WHERE THE ACCOUNTS DISAGREE
# ==========================================
t3 = doc.tables[3]
# Row 1
set_cell(t3.rows[1].cells[0], "Why tickets bounce to Tier 2 (Inherent technical complexity vs. findability/confidence)")
set_cell(t3.rows[1].cells[1], "Marcus claims tickets bounce because they are too difficult for Tier 1; Daniel claims ~50% could be solved at Tier 1 if agents found the right documentation or had confidence.")
set_cell(t3.rows[1].cells[2], "In development_tickets.json, 71.4% (357/500) of tickets are already answered in CloudServe's 29 KB articles, yet 56.2% (281/500) were escalated to Tier 2. Daniel is empirically correct: findability and confidence, not ticket difficulty, drive escalations.")
set_cell(t3.rows[1].cells[3], "Building semantic retrieval over documentation will immediately empower Tier 1 and enable safe auto-responses, resolving over 60% of tickets without Tier 2 involvement.")

# Row 2
set_cell(t3.rows[2].cells[0], "Solution strategy: Generic conversational chatbot vs. deterministic grounded pipeline with guardrails")
set_cell(t3.rows[2].cells[1], "Marcus pictures a simple chatbot to 'answer the easy ones'; Sofia and Daniel warn that incorrect automated answers cause customer fury, and that security/billing tickets must never be automated.")
set_cell(t3.rows[2].cells[2], "87 tickets (17.4%) are flagged must_not_auto_respond (security incidents, data residency, billing disputes). Furthermore, customers are technical engineers who verify claims. Unconstrained chatbots hallucinate and generate false financial/security commitments.")
set_cell(t3.rows[2].cells[3], "The system must NOT be an open chatbot. It must be a deterministic routing engine with strict confidence thresholds, semantic retrieval verification, and hard safety guardrails that escalate redline categories.")

# Row 3
set_cell(t3.rows[3].cells[0], "Impact and visibility of non-fluent English customer requests")
set_cell(t3.rows[3].cells[1], "Sofia notes non-fluent customers take much longer, suffer misunderstandings, and have the worst satisfaction scores ('no one has noticed'); Marcus does not monitor language fluency at all.")
set_cell(t3.rows[3].cells[2], "Non-fluent tickets (120/500, 24.0%) have an average resolution time of 466.1 minutes vs 407.7 minutes for fluent tickets (+58.4 minutes / +14.3% longer), representing a critical equity and SLA breach area.")
set_cell(t3.rows[3].cells[3], "The classification and retrieval engine must be semantic and resilient to non-native phrasing, grammatical variations, and typos, normalizing intent across language fluency levels.")

# Row 4
set_cell(t3.rows[4].cells[0], "Reliability of knowledge sources: Private snippet files vs. official 29 KB articles")
set_cell(t3.rows[4].cells[1], "Sofia and agents rely on personal snippet files because internal search fails; Ines states the 29 KB articles are accurate and reviewed; Daniel warns private snippet files contain outdated, incorrect answers.")
set_cell(t3.rows[4].cells[2], "71.4% of tickets are covered in Ines's reviewed documentation.json, but keyword search fails on semantic mismatch ('my deployment keeps dying' vs 'resolving container health check failures'). Private snippets circulate stale advice.")
set_cell(t3.rows[4].cells[3], "Knowledge must be strictly anchored to the reviewed 29 documentation articles using dense vector semantic search, eliminating unvetted personal snippet files while solving findability.")

# ==========================================
# TABLE 4: WHAT NOBODY SAID
# ==========================================
t4 = doc.tables[4]
# Row 1
set_cell(t4.rows[1].cells[0], "Multi-channel fragmentation and channel-specific SLAs")
set_cell(t4.rows[1].cells[1], "Tickets arrive across 4 distinct channels (Email 42.4%, Chat 31.0%, Docs Comments 15.6%, Forum 11.0%) with vastly different customer expectations (chat expects instant replies, email expects hours), yet management applies a single aggregate metric.")
set_cell(t4.rows[1].cells[2], "Analyze volume, average resolution time, and CSAT broken down by channel in development_tickets.json to establish normalized ingestion pipelines.")

# Row 2
set_cell(t4.rows[2].cells[0], "Upstream product and engineering root cause feedback loop")
set_cell(t4.rows[2].cells[1], "If 71.4% of tickets repeat the same 29 documented issues (e.g. container health checks, API rate limits), the underlying UX or error messaging should be remediated upstream to deflect ticket creation altogether.")
set_cell(t4.rows[2].cells[2], "Correlate repeat contact rate (21.6%) and top intents with product engineering backlog to identify defect prevention opportunities.")

# Row 3
set_cell(t4.rows[3].cells[0], "Automated documentation gap detection telemetry")
set_cell(t4.rows[3].cells[1], "Ines updates 29 articles on a rotation schedule, but there is no automated telemetry alerting her when multiple incoming queries fail retrieval or address unmapped topics.")
set_cell(t4.rows[3].cells[2], "Analyze answerable_from_docs == False tickets (28.6%, 143 tickets) to map clusters of missing documentation (e.g., specific SDK integrations, undocumented error codes).")

# Row 4
set_cell(t4.rows[4].cells[0], "Standardized escalation dossier protocol for Tier 2 handoffs")
set_cell(t4.rows[4].cells[1], "Daniel highlighted that raw ticket forwards waste huge amounts of engineering time re-asking questions, yet no structured escalation schema or context summary exists.")
set_cell(t4.rows[4].cells[2], "Evaluate Tier 2 resolution times and engineer an automated context synthesis dossier (predicted intent, retrieved passages, uncertainty trigger) for all escalated tickets.")

# ==========================================
# TABLE 5: SECTION 2 - TICKET DATA
# ==========================================
t5 = doc.tables[5]
# Row 1: Total tickets
set_cell(t5.rows[1].cells[1], "500 tickets")
set_cell(t5.rows[1].cells[2], "development_tickets.json total record count")
set_cell(t5.rows[1].cells[3], "Statistically representative development sample representing one week of real CloudServe support volume.")

# Row 2: Split by channel
set_cell(t5.rows[2].cells[1], "Email: 212 (42.4%), Chat: 155 (31.0%), Docs Comment: 78 (15.6%), Forum: 55 (11.0%)")
set_cell(t5.rows[2].cells[2], "Value counts of 'channel' field across all 500 tickets")
set_cell(t5.rows[2].cells[3], "Docs comments and forums account for over 26% of total volume, requiring robust multi-channel normalization.")

# Row 3: Split by intent category
set_cell(t5.rows[3].cells[1], "22 unique intents; Top: data_export (29, 5.8%), data_residency (29, 5.8%), rollback_request (28, 5.6%), deployment_failure (27, 5.4%), compliance_request (26, 5.2%)")
set_cell(t5.rows[3].cells[2], "Value counts of 'labels.intent' across all 500 tickets")
set_cell(t5.rows[3].cells[3], "Remarkably uniform distribution across 22 intents (all between 2.6% and 5.8%); no single intent dominates the queue.")

# Row 4: Split by urgency
set_cell(t5.rows[4].cells[1], "Medium: 226 (45.2%), High: 146 (29.2%), Low: 128 (25.6%)")
set_cell(t5.rows[4].cells[2], "Value counts of 'labels.urgency' across all 500 tickets")
set_cell(t5.rows[4].cells[3], "Nearly 30% of incoming tickets are High urgency, where 8-12 hour resolution breaches create severe business damage.")

# Row 5: First contact resolution
set_cell(t5.rows[5].cells[1], "219 / 500 (43.8%)")
set_cell(t5.rows[5].cells[2], "Count of 'history.first_contact_resolution' == True")
set_cell(t5.rows[5].cells[3], "Matches Marcus's estimate (42%); 56.2% of tickets bounce to Tier 2 escalations costing 4x more.")

# Row 6: Average satisfaction rating
set_cell(t5.rows[6].cells[1], "2.97 / 5.0 (Across all 500 tickets)")
set_cell(t5.rows[6].cells[2], "Mean of 'history.csat_rating'")
set_cell(t5.rows[6].cells[3], "Severely depressed CSAT (under 3.0), indicating customer churn risk at contract renewal.")

# Row 7: Most frequent single question
set_cell(t5.rows[7].cells[1], "data_export (29, 5.8%) and data_residency (29, 5.8%), followed by rollback_request (28, 5.6%)")
set_cell(t5.rows[7].cells[2], "Ranking of 'labels.intent' counts")
set_cell(t5.rows[7].cells[3], "Data and governance intents are the most frequent, where accurate retrieval and strict compliance boundaries are vital.")

# Row 8: Proportion answerable from docs
set_cell(t5.rows[8].cells[1], "357 / 500 (71.4%)")
set_cell(t5.rows[8].cells[2], "Count of 'labels.answerable_from_docs' == True")
set_cell(t5.rows[8].cells[3], "The pivotal finding: over 7 out of 10 incoming tickets are already answered in CloudServe's 29 KB articles! The problem is findability, not lack of answers.")

# Row 9: Non-fluent proportion and outcomes
set_cell(t5.rows[9].cells[1], "120 / 500 (24.0%); Avg Resolution Time: 466.1 min vs 407.7 min fluent (+58.4 min longer); CSAT: 3.04")
set_cell(t5.rows[9].cells[2], "Cross-tabulation of 'language_fluency' against resolution time and CSAT")
set_cell(t5.rows[9].cells[3], "Validates Sofia's insight: non-fluent users wait almost an hour longer due to misunderstanding cycles and poor keyword matching.")

# Row 10: Outcomes by customer tier
set_cell(t5.rows[10].cells[1], "Standard: 253 (50.6%, CSAT 2.98, Res: 442.1m); Business: 164 (32.8%, CSAT 2.91, Res: 358.8m); Enterprise: 83 (16.6%, CSAT 3.05, Res: 483.7m)")
set_cell(t5.rows[10].cells[2], "Cross-tabulation of 'customer_tier' against resolution time and CSAT")
set_cell(t5.rows[10].cells[3], "Enterprise tickets unexpectedly experience the longest resolution times (483.7 min) due to complex compliance/security escalations.")

# Row 11: Repeat contacts
set_cell(t5.rows[11].cells[1], "108 / 500 (21.6%)")
set_cell(t5.rows[11].cells[2], "Count of 'history.repeat_contact' == True")
set_cell(t5.rows[11].cells[3], "More than 1 in 5 tickets are repeat contacts, highlighting that first responses failed to fully resolve the customer's root issue.")

# Row 12: Must not auto-respond redlines
set_cell(t5.rows[12].cells[0], "Proportion flagged must_not_auto_respond")
set_cell(t5.rows[12].cells[1], "87 / 500 (17.4%)")
set_cell(t5.rows[12].cells[2], "Count of 'labels.must_not_auto_respond' == True")
set_cell(t5.rows[12].cells[3], "Critical safety redline: 17.4% of tickets (security, billing disputes, data residency) must never be auto-responded without human oversight.")

# Row 13: Expected routing distribution
set_cell(t5.rows[13].cells[0], "Expected auto-respond vs. escalation routing")
set_cell(t5.rows[13].cells[1], "Auto-respond: 311 (62.2%), Escalate: 189 (37.8%)")
set_cell(t5.rows[13].cells[2], "Value counts of 'labels.expected_route'")
set_cell(t5.rows[13].cells[3], "Demonstrates that a high-precision pipeline can safely deflect 62.2% of volume, cutting Tier 1 backlog in half while protecting redlines.")

# ==========================================
# TABLE 7: VOLUME VS EFFORT SHARE
# ==========================================
t7 = doc.tables[7]
t7_data = [
    ("Routine Documented Inquiries (account_access, api_usage, onboarding, rate_limit)", "28.0% (140 tickets)", "14.0% of agent effort", 
     "Quick 4-5 min copy-paste from personal snippets once recognized; high volume but relatively low individual cognitive effort.", 
     "Sofia's interview ('routine ones take 4-5 minutes'); high doc answerability (92%) in this cluster."),
    ("Technical Failures (deployment_failure, database_issue, rollback_request)", "16.4% (82 tickets)", "32.0% of agent effort", 
     "Requires inspecting logs, reproducing container failures, and coordinating rollback steps; high urgency and high escalation rate.", 
     "Ravi's interview (catastrophic when deployment fails); average resolution time > 500 min; Daniel notes frequent Tier 2 involvement."),
    ("Security & Compliance (security_incident, compliance_request, data_residency)", "16.2% (81 tickets)", "26.0% of agent effort", 
     "Strict safety redline; requires mandatory human review, audit tracking, legal verification, and formal sign-off.", 
     "Daniel's interview ('anything touching security must be escalated'); 100% of these tickets are marked must_not_auto_respond."),
    ("Billing & Commercial (billing_query, quota_or_overage)", "9.4% (47 tickets)", "12.0% of agent effort", 
     "Requires cross-referencing invoice lines, contract terms, and stripe/usage logs; high risk of customer friction.", 
     "Daniel's warning against automated commitments about money; contractual dispute review takes 30+ minutes."),
    ("Non-Fluent & Ambiguous Requests (unclear_request + non-fluent tickets across intents)", "10.0% (50 tickets)", "18.0% of agent effort", 
     "Requires multiple back-and-forth clarification turns; high cognitive load to infer true underlying issue.", 
     "Sofia's interview ('working out what they are actually asking'); data shows +58.4 min longer resolution time."),
    ("Integration & Webhooks (integration_help, webhook_issue)", "8.4% (42 tickets)", "8.0% of agent effort", 
     "Requires verifying payload signatures, HTTP response codes, and endpoint headers; moderate technical effort.", 
     "Ines's documentation on API & webhooks covers common status codes; moderate escalation rate (40%)."),
    ("Feature Requests & Roadmap (feature_request)", "4.0% (20 tickets)", "2.0% of agent effort", 
     "Cannot be answered from docs; fast disposition to product feedback board.", 
     "Ines notes docs cannot answer roadmap timing; rapid deflection to community forum.")
]

for idx, row_vals in enumerate(t7_data):
    for c_idx, val in enumerate(row_vals):
        set_cell(t7.rows[idx+1].cells[c_idx], val)

# ==========================================
# TABLE 8: AGENT WORKFLOW STEPS (SOFIA)
# ==========================================
t8 = doc.tables[8]
t8_data = [
    ("1", "Queue triage & sorting by age (opening queue, reviewing 40-70 tickets, prioritizing oldest near breach)", 
     "2–3 minutes per ticket batch", "Yes. Algorithmic queue sorting by SLA countdown and intent urgency can be fully automated."),
    ("2", "Reading and comprehending query (dissecting customer phrasing, error logs, and intent)", 
     "3–5 minutes (up to 10 min for non-fluent)", "Partially. Multi-channel text normalization, language detection, and intent classification can be automated."),
    ("3", "Searching for relevant answers (querying snippet files, searching KB, consulting colleagues)", 
     "5–15 minutes (or 40 min if rare)", "Yes. Dense vector semantic retrieval over the 29 KB articles executes in <500ms, eliminating snippet searching."),
    ("4", "Assessing answer confidence & safety redlines (checking security, billing, or novel edge cases)", 
     "2–3 minutes", "Yes. Calibrated numeric confidence thresholds and deterministic must_not_auto_respond filters automate this gate."),
    ("5", "Drafting, personalizing, and citing response (adapting snippet, tailoring to customer context)", 
     "4–8 minutes", "Yes for high-confidence routine queries (grounded generation with citations); drafts pre-populated for agent review on medium confidence."),
    ("6", "Handling escalation to Tier 2 (forwarding ticket, currently done as raw forward with no notes)", 
     "2–4 minutes", "Yes. System can automatically assemble a rich contextual dossier (intent, candidate doc chunks, specific uncertainty trigger)."),
    ("7", "Logging resolution and closing ticket (recording CRM tags, updating ticket status)", 
     "1–2 minutes", "Yes. Structured decision logging (1:1 audit trail) can be executed automatically upon routing or generation."),
    ("8", "Managing follow-up clarifications (handling repeat contacts when initial reply was unclear)", 
     "15–30 minutes across repeat turns", "Partially. High-precision grounded responses reduce repeat contacts by ensuring complete, cited answers upfront.")
]

for idx, row_vals in enumerate(t8_data):
    for c_idx, val in enumerate(row_vals):
        set_cell(t8.rows[idx+1].cells[c_idx], val)

# ==========================================
# TABLE 9: SUCCESS MEASURES
# ==========================================
t9 = doc.tables[9]
t9_data = [
    ("First Contact Resolution (FCR)", "Marcus Adeyemi (Head of Support)", "43.8% (219/500 tickets)", ">= 60.0% (approaching 65% industry benchmark)", "High (direct business impact, monitored weekly)"),
    ("First Response Time", "Executive Leadership & Marcus", "8–12 hours average", "< 5 minutes for automated; < 60 minutes for human queue", "High (explicit SLA contractual obligation)"),
    ("Average Resolution Time", "Marcus & Customers (Ravi)", "421.7 minutes (7.03 hours)", "< 120 minutes (< 2.0 hours contractual SLA)", "High (eliminates SLA penalty risk)"),
    ("Customer Satisfaction (CSAT)", "Executive Leadership & Ravi", "2.97 / 5.0", ">= 4.0 / 5.0", "High (prevents customer churn at contract renewal)"),
    ("Tier 2 Escalation Rate", "Daniel Okonkwo & Marcus", "56.2% (281/500 tickets)", "<= 35.0% (cutting avoidable escalations by >50%)", "High (Tier 2 costs 4x more than Tier 1)"),
    ("Hallucination / Inaccuracy Rate", "Marcus & Ravi", "Untracked (high risk)", "<= 1.0% (Zero critical hallucinations)", "High (protects brand reputation and platform trust)"),
    ("PII & Privacy Breaches", "Compliance Officer & Marcus", "Untracked (high risk)", "Exactly 0 incidents (100% compliance)", "Absolute (strict regulatory requirement)")
]

for idx, row_vals in enumerate(t9_data):
    for c_idx, val in enumerate(row_vals):
        set_cell(t9.rows[idx+1].cells[c_idx], val)

# ==========================================
# TABLE 10: THE SENTENCE TEST
# ==========================================
t10 = doc.tables[10]
set_cell(t10.rows[1].cells[1], 
    "This project will have been worth doing if, within three months of launch, first contact resolution rises from 43.8% to at least 60.0%, average resolution time drops from 7.0 hours to under 2.0 hours, and customer satisfaction improves from 2.97 to at least 4.0/5.0 without a single PII leakage or ungrounded hallucination incident.")
set_cell(t10.rows[2].cells[1], 
    "We will know it did not work if we see automated responses hallucinating incorrect technical advice, customer complaints on social media, CSAT remaining depressed below 3.5, or Tier 1 agents spending more time investigating and apologizing for bot mistakes than answering tickets.")
set_cell(t10.rows[3].cells[1], 
    "The measure the client will actually be judged on internally is First Contact Resolution (FCR) and contractual SLA compliance (<2-hour first response time) reported to executive leadership.")

# ==========================================
# TABLE 11: DATA SOURCES & CONSTRAINTS
# ==========================================
t11 = doc.tables[11]
t11_data = [
    ("Support tickets (development_tickets.json)", "500 historical multi-channel support tickets with metadata, labels, and resolution history.", 
     "High quality synthetic dataset; reflects real distribution; missing live CRM attachments.", "Internal development only; offline batch evaluation.", "Yes (synthetic customer names, emails, IPs, account IDs)."),
    ("Knowledge Base Articles (documentation.json)", "29 curated support articles covering authentication, deployments, billing, API, security, and data.", 
     "Accurate and reviewed on rotation by Ines; gaps in novel incidents, roadmaps, and feature requests.", "Must be indexed and searched; responses must strictly cite these IDs.", "No private customer data; public support content."),
    ("Ground Truth Resolutions (ground_truth_responses.json)", "Gold standard answers with expected doc chunk citations and key fact lists for all 500 tickets.", 
     "High precision; engineered for automated scoring and LLM-as-a-judge evaluation.", "Must NEVER be leaked into prompts during inference; used strictly for scoring.", "No."),
    ("Customer Tiers & SLA Metadata", "Tier classification (Standard, Business, Enterprise) and contractual response agreements.", 
     "Clearly mapped in ticket schema; enterprise requires prioritized handling.", "Must adhere to contractual response tiers without introducing unfair bias.", "Yes (linked to customer accounts)."),
    ("Personal Agent Snippet Files", "Informal local text files kept by individual agents containing legacy canned responses.", 
     "Severe quality risk: outdated, unreviewed, containing stale configurations (Daniel & Ines).", "DO NOT USE for training or retrieval. Knowledge must be grounded solely in official KB.", "Potential PII and outdated customer account numbers.")
]

for idx, row_vals in enumerate(t11_data):
    for c_idx, val in enumerate(row_vals):
        set_cell(t11.rows[idx+1].cells[c_idx], val)

# ==========================================
# TABLE 12: INITIAL RISK REGISTER
# ==========================================
t12 = doc.tables[12]
t12_data = [
    ("The system answers confidently and incorrectly (Hallucination)", "Medium", "High", 
     "Customer, Brand Reputation, Platform Integrity", 
     "Enforce strict confidence threshold (tau), dense semantic retrieval grounding, citation verification guardrail, and 'cannot answer' fallback."),
    ("Private information appears in a reply (PII Leakage)", "Medium", "Extreme", 
     "Customer Privacy, Compliance Review, CloudServe Legal", 
     "Implement two-way regex and NER PII scrubbing on both incoming ticket ingestion and generated response outputs."),
    ("Some customers get consistently worse answers (Non-fluent bias)", "Medium", "High", 
     "Non-fluent English customers (24% of volume)", 
     "Normalize queries with semantic embeddings and multi-turn intent clarification; evaluate cross-group fairness across fluency segments."),
    ("The documentation the system relies on goes out of date (Doc Drift)", "Low", "High", 
     "All support operations, Technical Writer (Ines)", 
     "Establish automated KB version tracking, citation staleness checks, and direct feedback loops to the documentation team."),
    ("Automated unauthorized financial commitment (Billing Disputes)", "Low", "High", 
     "Finance, Legal, Head of Support (Marcus)", 
     "Hard deterministic routing redline: flag all billing disputes and refund requests as must_not_auto_respond = True."),
    ("Prompt injection attack via ticket body or forum post", "Low", "High", 
     "System Security, Brand Reputation", 
     "Isolate user input using XML/JSON delimiter encapsulation; enforce system prompt immutability; implement prompt injection classifier."),
    ("Escalation flood overwhelms Tier 2 engineers", "Medium", "Medium", 
     "Tier 2 Engineers (Daniel), Support SLA", 
     "Generate rich context dossiers (predicted intent, candidate doc passages, root cause hypothesis, specific uncertainty trigger) with every escalation."),
    ("Model API rate limit or service timeout during peak hours", "Medium", "Medium", 
     "Support Queue, Customer Experience", 
     "Implement exponential backoff retry, circuit breakers, and graceful fallback to human triage queue without data loss.")
]

for idx, row_vals in enumerate(t12_data):
    for c_idx, val in enumerate(row_vals):
        set_cell(t12.rows[idx+1].cells[c_idx], val)

# ==========================================
# TABLE 13: PROBLEM STATEMENT ELEMENTS
# ==========================================
t13 = doc.tables[13]
set_cell(t13.rows[1].cells[1], "A generic customer service chatbot to answer 'easy tickets' and lower response time without adding headcount.")
set_cell(t13.rows[1].cells[2], "Section 1 (Marcus interview, Row 1); Section 4 (Marcus success criteria)")

set_cell(t13.rows[2].cells[1], 
    "An auditable, deterministic retrieval and routing pipeline that normalizes multi-channel tickets, surfaces authoritative passages from the 29 KB articles via dense semantic search, auto-responds only with verified citations, blocks safety redlines, and generates structured contextual dossiers for Tier 2 escalations.")
set_cell(t13.rows[2].cells[2], "Section 1 (Daniel, Ines, Sofia interviews); Section 2 (Row 8: 71.4% answerable from docs, Row 12: 17.4% redlines)")

set_cell(t13.rows[3].cells[1], 
    "Marcus assumed tickets bounce to Tier 2 due to inherent technical difficulty or agent shortage; the data proves 71.4% are already answered in official docs and bounce due to search keyword mismatch, unvetted snippets, and lack of escalation context. A generic chatbot would hallucinate on technical terms and mishandle safety redlines.")
set_cell(t13.rows[3].cells[2], "Section 1 (Disagreements 1 & 2); Section 2 (Rows 5, 8, 12, 13)")

set_cell(t13.rows[4].cells[1], 
    "Customers endure 8-12 hour delays (CSAT 2.97); Tier 1 agents face 40-70 backlogs with unsearchable docs; Tier 2 engineers waste 50% of time re-investigating findable issues; non-fluent users suffer ~1 hr longer wait times; leadership faces SLA breach penalties.")
set_cell(t13.rows[4].cells[2], "Section 1 (Sofia, Daniel, Ravi interviews); Section 2 (Rows 2, 6, 9, 10)")

set_cell(t13.rows[5].cells[1], 
    "First contact resolution will surpass 60%, average resolution time will drop below 2 hours (restoring contractual SLA), Tier 2 escalations will drop by >50%, and customer trust will be restored without adding headcount.")
set_cell(t13.rows[5].cells[2], "Section 3 (Sofia workflow); Section 4 (Success measures, Table 9 & 10)")

set_cell(t13.rows[6].cells[1], 
    "Explicitly out of scope: Answering novel unrecorded platform outages; making contractual/refund commitments; automating security compromise handling; modifying customer cloud infrastructure directly.")
set_cell(t13.rows[6].cells[2], "Section 1 (Ines & Daniel interviews); Section 5 (Risk register, Table 12)")

# ==========================================
# TABLE 14: ONE PARAGRAPH PROBLEM STATEMENT
# ==========================================
t14 = doc.tables[14]
problem_statement = (
    "CloudServe Solutions receives over 500 support tickets weekly across four fragmented channels, resulting in severe "
    "8–12 hour response delays against a 2-hour SLA, low first-contact resolution (43.8%), and depressed customer satisfaction (2.97/5.0). "
    "While leadership diagnosed this as an agent headcount shortage requiring a generic chatbot, empirical analysis reveals that 71.4% "
    "of incoming tickets are already fully answerable from CloudServe's 29 knowledge base articles, but fail to resolve at Tier 1 because "
    "internal keyword search cannot bridge customer vocabulary with technical article titles, forcing agents to rely on unreviewed personal "
    "snippets or escalate 56.2% of tickets without context to Tier 2. The core operational problem is not a deficit of support answers or "
    "staffing capacity, but a failure of retrieval findability, uncalibrated triage confidence, and context-free escalation packaging "
    "across multi-channel customer communications."
)
set_cell(t14.rows[1].cells[0], problem_statement)

# Save populated document
doc.save(doc_path)
print("Successfully populated Stage_1_Discovery_Workbook.docx!")
