import asyncio
import json
import logging
from core_brain import get_omnicortex_brain, FakeMessage

logging.basicConfig(level=logging.INFO)

def run_test():
    print("\n--- OMNICORTEX HEADLESS DIAGNOSTIC TEST (V2.3 ACRONYM MAPPING) ---")
    brain = get_omnicortex_brain()
    
    test_q = "nbpisf yearly comparision progresss and percentages"
    print(f"\n[TEST] Testing Query: '{test_q}'")
    
    test_history = [{"role": "user", "content": test_q}]
    response = brain.invoke({"messages": [FakeMessage(test_history[0]["content"])]})
    
    try:
        data = json.loads(response["messages"][-1].content)
        print("\n\n=== VERDICT ===")
        print(data.get("verdict"))
        print("\n=== GRAHAM ANALYSIS (Should have actual metrics) ===")
        print(data.get("graham_analysis"))
    except Exception as e:
        print("FAILED TO PARSE Response.")
        print(response["messages"][-1].content)

if __name__ == "__main__":
    run_test()
