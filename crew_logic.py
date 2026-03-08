import os
import google.generativeai as genai


def initialize_llm():
    """
    Initializes the Google Gemini 3.1 Flash-Lite model.
    This is used as a standalone LLM for any non-OmniCortex tasks
    (e.g., if CrewAI is ever re-enabled for batch processing).
    
    For the main OmniCortex brain, use core_brain.py directly.
    
    Requires GOOGLE_API_KEY environment variable.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not found.")
        print("Set it via:")
        print("  PowerShell:     $env:GOOGLE_API_KEY='your_key_here'")
        print("  Command Prompt: set GOOGLE_API_KEY=your_key_here")
        print("  Mac/Linux:      export GOOGLE_API_KEY='your_key_here'")
        return None

    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite-preview"
    )
    
    print("[LLM] Gemini 3.1 Flash-Lite initialized successfully.")
    return model


if __name__ == "__main__":
    print("Testing Gemini 3.1 Flash-Lite Initialization...")
    test_model = initialize_llm()
    if test_model:
        response = test_model.generate_content("What is Benjamin Graham's Margin of Safety?")
        print(f"\nTest Response:\n{response.text[:500]}")
