import os
import google.generativeai as genai
from core_brain import fetch_sql_metrics

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

user_input = "NBP Islamic Stock Fund yearly performance"

graham_prompt = f"""
You are the Graham Fundamental Analyst. Your ONLY tool is fetch_sql_metrics.
You must use fetch_sql_metrics to get fundamental data for the user's query: '{user_input}'.

TOOL CRITICAL RULE: Before passing the argument to `fetch_sql_metrics`, you MUST isolate strictly the asset or fund name (e.g. 'NBP Islamic Stock Fund', 'HUBC.KA'). NEVER pass conversational words like 'compare', 'percentages', 'yearly', or the tool will crash. Only pass the isolated asset name/ticker!

If the query is general, use fetch_sql_metrics for related fundamental data or explain that you focus on specific asset fundamentals.
Return a purely data-driven fundamental analysis. Do not include conversational filler.

TRANSLATION RULE: You MUST write your analysis entirely in layman's Roman Urdu. 
Simplify complex terms (e.g. use "aik hisse ki qeemat" for NAV, "mahina-ba-mahina munafa" for MoM, "saalana munafa" for annualized return). Explain the numbers so an everyday person can understand.

FORMATTING RULES:
1. NO FLUFF: Do not use greetings or conversational filler. Start analysis immediately.
2. BULLET POINTS: Format output strictly using short bullet points (*).
3. WORD LIMIT: Your entire response must not exceed 40 words.
"""

graham_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=[fetch_sql_metrics]
)
chat1 = graham_model.start_chat()
resp1 = chat1.send_message(graham_prompt)
if resp1.parts and hasattr(resp1.parts[0], 'function_call'):
    fc = resp1.parts[0].function_call
    print(f"Agent 1 wants to call: {fc.name} with args: {dict(fc.args)}")
else:
    print("Agent 1 didn't call a function. Text:", resp1.text)
