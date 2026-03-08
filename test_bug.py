import asyncio
import json
import logging
from core_brain import get_omnicortex_brain, FakeMessage
from google.cloud import bigquery
import os

logging.basicConfig(level=logging.INFO)

def run_test():
    print("\n--- OMNICORTEX HEADLESS DIAGNOSTIC TEST ---")
    brain = get_omnicortex_brain()
    
    test_q = "NBP Islamic Stock Fund yearly performance"
    print(f"\n[TEST] Testing Query: '{test_q}'")
    
    # We will invoke the brain and check the response
    test_history = [{"role": "user", "content": test_q}]
    response = brain.invoke({"messages": [FakeMessage(test_history[0]["content"])]})
    
    try:
        data = json.loads(response["messages"][-1].content)
        print("\n\n=== VERDICT ===")
        print(data.get("verdict"))
        print("\n=== GRAHAM ANALYSIS ===")
        print(data.get("graham_analysis"))
        print("\n=== MACRO ANALYSIS ===")
        print(data.get("macro_analysis"))
    except Exception as e:
        print("FAILED TO PARSE Response.", e)
        print(response["messages"][-1].content)

if __name__ == "__main__":
    run_test()
