import os
import time
from langchain_groq import ChatGroq

def initialize_llm():
    """
    Initializes the Groq LLM client using Meta's Llama 3 models.
    Requires GROQ_API_KEY environment variable.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("WARNING: GROQ_API_KEY environment variable not found.")
        print("Please set it in your terminal before running the AI!")
        print("  Command Prompt: set GROQ_API_KEY=your_key_here")
        print("  PowerShell:     $env:GROQ_API_KEY='your_key_here'")
        print("  Mac/Linux:      export GROQ_API_KEY='your_key_here'")
        return None

    # Using LLaMA 3 8B model. It is exceptionally fast, mathematically capable, 
    # and has generous rate limits on the Groq free tier.
    # (Optional upgrade: "llama3-70b-8192" if higher reasoning is needed later but beware stricter limits)
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama3-8b-8192", 
        temperature=0.1, # Keep temperature low to prevent hallucination in financial analysis
        max_retries=3    # Auto-retry softly if rate limit temporarily hits
    )
    
    print("Successfully initialized Groq LLM (Llama 3).")
    return llm

def apply_rate_limit_delay(seconds: int = 5):
    """
    Groq free tier has sharp Requests Per Minute (RPM) limits (often 30 RPM).
    Call this helper between agent tasks or API calls to prevent 429 errors.
    """
    print(f"[RATE LIMIT] Pausing for {seconds} seconds to respect Groq API limits...")
    time.sleep(seconds)
    print("[RATE LIMIT] Resuming.")

if __name__ == "__main__":
    print("Testing Groq LLM Initialization...")
    test_llm = initialize_llm()
    if test_llm:
        print("The LLM is ready to power The Graham Analyst and The CIO!")
        apply_rate_limit_delay(2)
