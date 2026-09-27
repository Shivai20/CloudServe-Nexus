import docx

def inspect_tables(filepath):
    doc = docx.Document(filepath)
    print(f"\n--- Tables in {filepath} ---")
    for i, table in enumerate(doc.tables):
        print(f"Table {i}:")
        for row in table.rows[:2]:  # Print first two rows
            print([cell.text for cell in row.cells])
        print("---")

inspect_tables('FDE_Capstone_Complete/Capstone_Pack/04_Submission/Effort_Log.docx')
inspect_tables('FDE_Capstone_Complete/Capstone_Pack/03_Reference/Governance_Framework.docx')
