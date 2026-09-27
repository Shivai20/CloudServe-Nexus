from docx import Document

def populate_stage4(docx_path, output_path):
    doc = Document(docx_path)
    
    # Table 1: Availability
    table1 = doc.tables[1]
    for i in range(1, 4):
        table1.cell(i, 1).text = "40"
        table1.cell(i, 2).text = "FDE Capstone Project"
        table1.cell(i, 3).text = "None"

    # Table 3: Backlog
    table3 = doc.tables[3]
    backlog = [
        ("B-01", "Environment and dependency setup", "2", "Must", "None", "pytest runs without errors"),
        ("B-02", "Data loading and normalisation", "4", "Must", "B-01", "500 tickets loaded into Pydantic models"),
        ("B-03", "Document chunking and embedding", "4", "Must", "B-01", "29 KB articles parsed and chunked"),
        ("B-04", "Vector store and retrieval", "4", "Must", "B-03", "Returns correct chunk IDs for test queries"),
        ("B-05", "LLM Intent Classification Node", "4", "Must", "B-02", "Outputs valid JSON matching 22 intents"),
        ("B-06", "LLM Safety Guardrails Node", "3", "Must", "B-02", "Successfully flags PII/redline tickets"),
        ("B-07", "Routing Logic Engine", "3", "Must", "B-05, B-06", "Deterministically routes to generation or escalation"),
        ("B-08", "Grounded Generation Node", "6", "Must", "B-04, B-07", "Generates answers with citations only"),
        ("B-09", "Pipeline Integration & Fault Tolerance", "6", "Must", "B-04, B-08", "End-to-end flow runs without crashing on timeouts"),
        ("B-10", "Audit Logging", "2", "Must", "B-09", "Log file reconciles 1:1 with input tickets"),
        ("B-11", "Unattended Evaluation CLI", "2", "Must", "B-10", "--input and --output flags work unattended"),
        ("B-12", "Testing & Metrics Reporting", "4", "Must", "B-11", "Markdown report generated automatically")
    ]
    
    while len(table3.rows) < len(backlog) + 1:
        table3.add_row()
        
    for i, (b_id, item, hours, prio, dep, dod) in enumerate(backlog):
        row = table3.rows[i+1]
        row.cells[0].text = b_id
        row.cells[1].text = item
        row.cells[2].text = hours
        row.cells[3].text = prio
        row.cells[4].text = dep
        row.cells[5].text = dod

    # Table 4: Week 1 Sprint
    table4 = doc.tables[4]
    w1_plan = [
        ("Monday", "B-01 (Setup) & B-02 (Data loading)", "6", "Pydantic schema mismatch with raw data"),
        ("Tuesday", "B-03 (Chunking) & B-04 (Vector Store)", "8", "Embedding model API limits"),
        ("Wednesday", "B-05 (Classification Node)", "4", "Prompt drift causing invalid JSON"),
        ("Thursday", "B-06 (Guardrails) & B-07 (Routing)", "6", "Edge cases in redline definitions"),
        ("Friday", "B-08 (Grounded Generation) started", "6", "Hallucinations bypassing constraints")
    ]
    for i, (day, what, hrs, risk) in enumerate(w1_plan):
        row = table4.rows[i+1]
        row.cells[0].text = day
        row.cells[1].text = what
        row.cells[2].text = hrs
        row.cells[3].text = risk

    # Table 5: Week 2 Sprint
    table5 = doc.tables[5]
    w2_plan = [
        ("Monday", "B-08 (Grounded Generation) finished", "6", "Latency issues on large contexts"),
        ("Tuesday", "B-09 (Integration & Fault Tolerance)", "8", "State mismatch between nodes"),
        ("Wednesday", "B-10 (Audit Log) & B-11 (CLI)", "4", "Logging concurrency issues"),
        ("Thursday", "B-12 (Testing & Metrics)", "8", "Pytest suite failing on edge cases"),
        ("Friday", "Final Review and Documentation", "4", "Unmet A1-A12 criteria")
    ]
    for i, (day, what, hrs, risk) in enumerate(w2_plan):
        row = table5.rows[i+1]
        row.cells[0].text = day
        row.cells[1].text = what
        row.cells[2].text = hrs
        row.cells[3].text = risk

    # Table 6: Scope Cutting
    table6 = doc.tables[6]
    cuts = [
        ("Complex query re-writing", "1st to go", "Lower retrieval accuracy for vague tickets.", "Documented as a future enhancement in V2."),
        ("Multi-threading batch CLI", "2nd to go", "Evaluation run will take longer (sequential processing).", "Noted in NFRs that latency is compromised for stability."),
        ("Automated hallucination detection metric", "3rd to go", "Metrics report relies more on manual spot checks for accuracy.", "Acknowledged in the metrics report limitations.")
    ]
    while len(table6.rows) < len(cuts) + 1:
        table6.add_row()
        
    for i, (item, order, cons, report) in enumerate(cuts):
        row = table6.rows[i+1]
        row.cells[0].text = item
        row.cells[1].text = order
        row.cells[2].text = cons
        row.cells[3].text = report

    doc.save(output_path)
    print(f"Successfully saved Sprint Plan to {output_path}")

if __name__ == "__main__":
    import sys
    populate_stage4(sys.argv[1], sys.argv[1])
