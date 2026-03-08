import asyncio
import json
import logging
from core_brain import get_omnicortex_brain, FakeMessage

logging.basicConfig(level=logging.INFO)

def run_headless_tests():
    print("\n--- OMNICORTEX HEADLESS DIAGNOSTIC TEST ---")
    brain = get_omnicortex_brain()
    
    # --- TEST 1: The Regex & SQL Path (Past/Fundamental Analysis) ---
    print("\n[TEST 1] Testing Fundamental Path w/ Regex Cleanup 'NBP Islamic Stock Fund (NBPI SF)'...")
    test1_history = [
        {"role": "user", "content": "Analyze NBP Islamic Stock Fund (NBPI SF)"}
    ]
    response1 = brain.invoke({"messages": [FakeMessage(test1_history[0]["content"])]})
    try:
        data1 = json.loads(response1["messages"][-1].content)
        print("Verdict:", data1.get("verdict"))
        print("Graham Analysis Snippet:", str(data1.get("graham_analysis"))[:100] + "...")
        print("Test 1 Status: PASS if valid JSON & Roman Urdu.")
    except Exception as e:
        print(f"Test 1 FAILED. Output was not valid JSON or crashed: {str(e)}")
        print("Raw Output:", response1["messages"][-1].content)

    # --- TEST 2: Macro Live Path (Live Market Check) ---
    print("\n[TEST 2] Testing Live Macro Synthesis...")
    test2_history = [
        {"role": "user", "content": "What is the SBP and inflation doing right now? And how is KSE-100?"}
    ]
    response2 = brain.invoke({"messages": [FakeMessage(test2_history[0]["content"])]})
    try:
        data2 = json.loads(response2["messages"][-1].content)
        print("Verdict:", data2.get("verdict"))
        print("Macro Analysis Snippet:", str(data2.get("macro_analysis"))[:100] + "...")
        print("Test 2 Status: PASS if valid JSON & Roman Urdu.")
    except Exception as e:
        print(f"Test 2 FAILED. Output was not valid JSON or crashed: {str(e)}")
        print("Raw Output:", response2["messages"][-1].content)

    # --- TEST 3: Edge Case / Hallucination Halt (Bad/Missing Data) ---
    print("\n[TEST 3] Testing Anti-Hallucination Halt (Fake Asset 'ZXCBNV.KA')...")
    test3_history = [
        {"role": "user", "content": "Analyze ZXCBNV.KA"}
    ]
    response3 = brain.invoke({"messages": [FakeMessage(test3_history[0]["content"])]})
    try:
        data3 = json.loads(response3["messages"][-1].content)
        verdict = data3.get("verdict").upper()
        print("Verdict:", verdict)
        if "ERROR" in verdict or "INSUFFICIENT" in verdict:
            print("Test 3 Status: PASS. AI successfully halted instead of hallucinating.")
        else:
            print(f"Test 3 FAILED. AI tried to give a real verdict ({verdict}) on fake data.")
    except Exception as e:
        print(f"Test 3 FAILED. Output was not valid JSON: {str(e)}")
        print("Raw Output:", response3["messages"][-1].content)

if __name__ == "__main__":
    run_headless_tests()
