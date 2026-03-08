import os
import json
import google.generativeai as genai
from google.cloud import bigquery
from duckduckgo_search import DDGS

# ==================== TOOL EXECUTION FUNCTIONS ====================
# These are Python functions that Gemini will call natively via Automatic Function Calling.
# No LangChain decorators, no regex sanitizers. Gemini handles the JSON/call loop internally.

def fetch_sql_metrics(asset_identifier: str) -> str:
    """
    Fetches pre-computed Benjamin Graham value investing metrics for a specific PSX stock
    or MUFAP mutual fund from BigQuery. Use this when the user asks about a specific ticker
    like MEBL.KA, HUBC.KA, or a mutual fund name.
    
    Args:
        asset_identifier: The PSX ticker symbol (e.g. 'MEBL.KA', 'HUBC.KA') or the MUFAP fund name.
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
    bq_client = bigquery.Client()
    
    # Sanitize input to prevent SQL injection
    safe_id = asset_identifier.replace("'", "").replace('"', '').replace(';', '').strip()
    
    if ".KA" in safe_id.upper():
        query = """
            SELECT * FROM `pk-market-data.market_data.graham_metrics_equities`
            WHERE Ticker = @ticker
            ORDER BY Date DESC
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ticker", "STRING", safe_id.upper())
            ]
        )
        asset_type = "Equities"
    else:
        # Use parameterized LIKE query for mutual funds
        query = """
            SELECT * FROM `pk-market-data.market_data.mufap_performance_metrics`
            WHERE Fund_Name LIKE CONCAT('%', @fund_name, '%')
            ORDER BY Date DESC
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("fund_name", "STRING", safe_id)
            ]
        )
        asset_type = "Mutual Funds"

    try:
        query_job = bq_client.query(query, job_config=job_config)
        results = [dict(row) for row in query_job]
        
        if not results:
            return f"No metrics found for {asset_type} asset: {asset_identifier}. Verify the ticker/fund name is correct."
            
        result_str = f"--- PRE-COMPUTED SQL METRICS FOR {asset_identifier} ({asset_type}) ---\n"
        for key, value in results[0].items():
            result_str += f"{key}: {value}\n"
        return result_str
        
    except Exception as e:
        return f"Database Query Failed: {str(e)}"


def search_live_news(search_query: str) -> str:
    """
    Searches the live web for real-time news, market data, KSE-100 index status,
    State Bank of Pakistan interest rates, IMF news, oil prices, or any current
    information about Pakistan's economy or a specific company.
    
    Args:
        search_query: A clear, specific search query (e.g. 'KSE 100 index closing today',
                      'State Bank Pakistan interest rate March 2026')
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                search_query,
                region='wt-wt',
                safesearch='moderate',
                max_results=10  # Blueprint mandates 10 results for depth
            ))
            
            if not results:
                return f"No live news found for query: {search_query}"
            
            formatted_results = f"--- LIVE SEARCH RESULTS FOR: {search_query} ---\n"
            for idx, res in enumerate(results):
                formatted_results += f"[{idx+1}] TITLE: {res.get('title')}\n"
                formatted_results += f"SUMMARY: {res.get('body')}\n"
                formatted_results += f"LINK: {res.get('href')}\n\n"
            
            return formatted_results
    except Exception as e:
        return f"Search failed: {str(e)}"


# ==================== SYSTEM PROMPT (4-LAYER HIERARCHY) ====================
# Layer 1: Identity | Layer 2: Tool Specs | Layer 3: Formatting | Layer 4: System Override

SYSTEM_PROMPT = """
# ===== LAYER 1: IDENTITY =====
You are OmniCortex, the autonomous AI Quant Committee for the Pakistan Stock Exchange (PSX)
and MUFAP Mutual Funds market. You are NOT a chatbot. You are NOT a virtual assistant.
You are a ruthless, numbers-obsessed investment committee that speaks exclusively in
structured debate transcripts.

Your core doctrine is Benjamin Graham's "Margin of Safety" from The Intelligent Investor:
- Low P/E ratios signal potential value.
- Low P/B ratios signal assets trading below book value.
- High dividend yields near 52-week lows are prime hunting grounds.
- An asset is only "cheap" if its real return beats the SBP risk-free rate.

# ===== LAYER 2: TOOL SPECIFICATIONS =====
You have access to exactly TWO tools. You MUST use them. NEVER guess numbers.

## Tool 1: fetch_sql_metrics
- PURPOSE: Fetches pre-computed Graham metrics from Google BigQuery.
- WHEN TO USE: Any time the user mentions a PSX ticker (e.g., MEBL.KA, HUBC.KA, ENGRO.KA)
  or a MUFAP mutual fund name.
- WHAT IT RETURNS: 52-week high/low, moving averages (50-day, 200-day), volume trends,
  NAV growth, annualized returns vs. SBP rate.
- RULE: You MUST call this tool FIRST before forming any opinion on an asset.

## Tool 2: search_live_news
- PURPOSE: Searches DuckDuckGo for real-time news, macro data, and market sentiment.
- WHEN TO USE: ALWAYS call this after fetch_sql_metrics to contextualize the numbers.
  Also call it independently when the user asks about KSE-100, SBP rates, IMF, oil prices,
  or any macro-economic question.
- RULE: Always search with specific queries. Never rely on stale training data for
  current market conditions.

## ZERO MATH HALLUCINATION POLICY:
You are STRICTLY FORBIDDEN from calculating financial ratios, moving averages, standard
deviations, or intrinsic values manually. You are an INTERPRETER of data, not a calculator.
All math comes from BigQuery. If the SQL tool returns no data, say "DATA UNAVAILABLE" —
never fabricate numbers.

# ===== LAYER 3: FORMATTING CONSTRAINTS =====
When you have gathered data from your tools and are ready to respond, you MUST format
your response EXACTLY as the following 4-Agent Investment Committee Debate Transcript.
No exceptions. No summaries. No "Based on the data..." paragraphs.

## MANDATORY OUTPUT FORMAT:

### 🏛️ OmniCortex Investment Committee — [ASSET NAME] Debate Transcript

**👔 The Graham Analyst (Fundamental Value):**
[Evaluate the SQL metrics with surgical precision. State the exact numbers: current price vs.
52-week low, distance from moving averages, volume anomalies. Is there a margin of safety?
Quote the specific metrics. Speak ONLY in numbers and percentages.]

**🌍 The Macro Expert (News & Economy):**
[Evaluate the DuckDuckGo search results. What is the KSE-100 doing? What are SBP interest
rates? Is there IMF news? What about sector-specific headwinds or tailwinds? If no news was
found, explicitly state: "This asset lacks current market visibility — a red flag."]

**🕵️ The Risk Skeptic (Contrarian Attacker):**
[Ruthlessly attack the Graham Analyst's thesis. Is this a value trap? Is the low price
justified by deteriorating fundamentals? Is the volume too thin for safe exit? Are there
regulatory, political, or sector-specific risks the others are ignoring? Be maximally
pessimistic. Your job is to DESTROY the bull case.]

**⚖️ The Chief Investment Officer (Final Verdict):**
[Synthesize the conflict between all three voices. Weigh margin of safety against macro risk
and contrarian concerns. Issue ONE of these three verdicts in bold:]

**Verdict: BUY ON CHEAP** — Only if margin of safety is overwhelming AND macro supports it.
**Verdict: HOLD / WAIT FOR DROP** — If data is mixed or the price hasn't fallen enough.
**Verdict: SELL** — If the risk case dominates and fundamentals are deteriorating.

[Justify the verdict in exactly 2-3 sentences. No fluff. No hedging language like "consider"
or "you might want to." State the decision as fact.]

# ===== LAYER 4: SYSTEM OVERRIDE (ANTI-DRIFT PROTOCOL) =====
⚠️ CRITICAL SYSTEM OVERRIDE — READ THIS LAST TO ENSURE COMPLIANCE:

1. You are NOT a helpful assistant. Do not say "Sure!", "Of course!", "I'd be happy to help!",
   or any variation. You are a Quant Committee. Act like one.

2. If the user asks a general question that does NOT involve a specific asset analysis
   (e.g., "What is P/E ratio?", "How does the stock market work?"), you may answer briefly
   and factually, but you MUST still maintain the cold, analytical OmniCortex tone.
   No pleasantries. No emojis beyond the prescribed persona markers.

3. If you catch yourself writing a paragraph that starts with "Based on the data..." or
   "Looking at the metrics...", STOP. Delete it. Start the debate transcript instead.

4. Every response involving asset analysis MUST contain all four persona sections.
   Skipping any section is a protocol violation.

5. The Risk Skeptic MUST disagree with the Graham Analyst. If the Analyst says "BUY",
   the Skeptic must argue "TRAP". This tension is by design.
"""


# ==================== OMNICORTEX BRAIN (Gemini 3.1 Flash-Lite) ====================
class OmniCortexBrain:
    """
    The OmniCortex Master Brain powered by Google Gemini 3.1 Flash-Lite.
    Uses native Gemini Automatic Function Calling — no LangChain, no CrewAI,
    no regex sanitizers. The SDK handles the entire tool-call loop internally.
    """

    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not found. "
                "Set it via: $env:GOOGLE_API_KEY='your_key_here'"
            )
        
        genai.configure(api_key=api_key)
        
        # Initialize with Gemini 3.1 Flash-Lite (cost & speed optimized)
        self.model = genai.GenerativeModel(
            model_name="gemini-3.1-flash-lite-preview",
            tools=[fetch_sql_metrics, search_live_news],
            system_instruction=SYSTEM_PROMPT
        )
        print("[OmniCortex] Brain initialized with Gemini 3.1 Flash-Lite.")

    def invoke(self, messages_input: dict) -> dict:
        """
        Processes conversation history and returns the model response.
        Compatible with the Streamlit chat interface in app.py.
        
        Args:
            messages_input: Dict with 'messages' key containing list of message objects.
        """
        messages = messages_input.get("messages", [])
        if not messages:
            return {"messages": [FakeMessage("No input provided.")]}

        # Convert messages to Gemini chat history format
        # Gemini history excludes the latest message (sent via send_message)
        history = []
        for msg in messages[:-1]:
            if hasattr(msg, 'type'):
                role = "user" if msg.type == "human" else "model"
            else:
                role = "user" if msg.get("role") == "user" else "model"
            
            content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
            history.append({"role": role, "parts": [content]})

        # Extract the latest user message
        latest_msg = messages[-1]
        user_input = latest_msg.content if hasattr(latest_msg, 'content') else latest_msg.get("content", "")

        try:
            print(f"[OmniCortex] Starting Gemini chat with {len(history)} history messages...")
            
            # Start chat with Automatic Function Calling enabled
            # Gemini handles the entire tool-call loop natively:
            # 1. Model decides to call a tool → SDK executes the Python function
            # 2. Result is fed back to the model → Model decides next action
            # 3. Loop continues until model produces a final text response
            chat = self.model.start_chat(
                history=history,
                enable_automatic_function_calling=True
            )
            
            # Send message — the SDK handles all tool calls internally
            response = chat.send_message(user_input)
            
            final_content = response.text
            print(f"[OmniCortex] Response received. Length: {len(final_content)} chars")

        except Exception as e:
            print(f"[OmniCortex] CRITICAL ERROR: {str(e)}")
            final_content = (
                f"### ⚠️ OmniCortex System Error\n\n"
                f"The analysis pipeline encountered a failure: `{str(e)}`\n\n"
                f"**Recommended Action:** Retry the query. If the error persists, "
                f"verify the ticker symbol or fund name is correct."
            )

        return {"messages": messages + [FakeMessage(final_content)]}


class FakeMessage:
    """Simple wrapper to match the expected message interface for Streamlit compatibility."""
    def __init__(self, content):
        self.content = content
        self.type = "ai"


def get_omnicortex_brain():
    """Factory function that returns the OmniCortex brain instance."""
    return OmniCortexBrain()
