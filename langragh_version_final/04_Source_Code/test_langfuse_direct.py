import os
import logging
from langfuse import Langfuse

# Configure logging to see all output
logging.basicConfig(level=logging.DEBUG)

def direct_test():
    print("Testing Langfuse Direct SDK...")
    
    # Initialize Langfuse client directly
    langfuse = Langfuse()
    
    print("Creating a test trace...")
    trace = langfuse.trace(
        name="direct_sdk_test",
        session_id="test-session-123",
        input={"test": "Hello Langfuse"}
    )
    
    print("Adding a span...")
    span = trace.span(
        name="test-span",
        input="Span input",
        output="Span output"
    )
    
    print("Flushing...")
    langfuse.flush()
    print("Flush complete. Check your dashboard for 'direct_sdk_test' trace.")

if __name__ == "__main__":
    direct_test()
