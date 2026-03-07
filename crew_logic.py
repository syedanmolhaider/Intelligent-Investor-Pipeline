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

    # Using LLaMA 3.3 70B model. It is exceptionally smart and solves XML tool hallucinations.
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile", 
        temperature=0.1, # Keep temperature low to prevent hallucination in financial analysis
        max_retries=3    # Auto-retry softly if rate limit temporarily hits
    )
    
    # WORKAROUND FOR CREWAI 0.108+ ARCHITECTURE:
    # CrewAI has deep integrations with OpenAI for tracing, evaluation, and internal reasoning
    # checks. We completely hijack the OpenAI base url here and point it strictly to Groq's
    # OpenAI-compatible endpoint. This solves all "Incorrect API key" errors.
    os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
    os.environ["OPENAI_MODEL_NAME"] = "llama-3.3-70b-versatile"
    os.environ["OPENAI_API_KEY"] = api_key
        
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
