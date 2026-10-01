import os
from src.pipeline import SupportPipeline

def test_langfuse():
    # Make sure we have the keys set
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        print("Please set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to test tracing.")
        return

    print("Initializing Pipeline...")
    # Initialize the pipeline (using our threshold)
    pipeline = SupportPipeline(threshold=0.55)

    print("Processing a sample ticket...")
    # Sample ticket that should trigger auto-respond or escalate depending on retrieval
    sample_ticket = {
        "ticket_id": "TEST-100",
        "channel": "email",
        "subject": "How do I reset my password?",
        "body": "Hi, I forgot my password and cannot log in. Can you help me reset it?",
        "customer_id": "CUST-001"
    }

    result = pipeline.process_ticket(sample_ticket)
    
    print("\n--- Pipeline Result ---")
    print(f"Action Taken: {result.action}")
    print(f"Classified Intent: {result.classified_intent}")
    print(f"Confidence: {result.confidence}")
    print(f"Reason: {result.reason}")
    print("-----------------------")
    
    print("\nCheck your Langfuse dashboard! You should see a new trace for this pipeline run.")

if __name__ == "__main__":
    test_langfuse()
