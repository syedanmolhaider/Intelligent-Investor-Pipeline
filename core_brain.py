import os
import json
from datetime import datetime
import google.generativeai as genai
from google.cloud import bigquery
from ddgs import DDGS

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
        # For mutual funds, try the performance view first, fall back to raw NAV table
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
            # For mutual funds, try the raw table as fallback
            if asset_type == "Mutual Funds":
                fallback_query = """
                    SELECT Date, Fund_Name, Category, NAV
                    FROM `pk-market-data.market_data.mufap_daily_nav`
                    WHERE Fund_Name LIKE CONCAT('%', @fund_name, '%')
                    ORDER BY Date DESC
                    LIMIT 5
                """
                fallback_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("fund_name", "STRING", safe_id)
                    ]
                )
                fallback_job = bq_client.query(fallback_query, job_config=fallback_config)
                fallback_results = [dict(row) for row in fallback_job]
                if fallback_results:
                    result_str = f"--- RAW NAV DATA FOR {asset_identifier} (Mutual Funds - Fallback) ---\n"
                    for row in fallback_results:
                        for key, value in row.items():
                            result_str += f"{key}: {value}\n"
                        result_str += "---\n"
                    return result_str
            
            return (
                f"No SQL metrics found for {asset_type} asset: {asset_identifier}. "
                f"The database has no records matching this name. "
                f"YOU MUST STILL PROCEED: Call search_live_news to find current information about this asset from the web."
            )
            
        result_str = f"--- PRE-COMPUTED SQL METRICS FOR {asset_identifier} ({asset_type}) ---\n"
        for key, value in results[0].items():
            result_str += f"{key}: {value}\n"
        return result_str
        
    except Exception as e:
        # On query failure, try raw table fallback for mutual funds
        if asset_type == "Mutual Funds":
            try:
                fallback_query = """
                    SELECT Date, Fund_Name, Category, NAV
                    FROM `pk-market-data.market_data.mufap_daily_nav`
                    WHERE Fund_Name LIKE CONCAT('%', @fund_name, '%')
                    ORDER BY Date DESC
                    LIMIT 5
                """
                fallback_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("fund_name", "STRING", safe_id)
                    ]
                )
                fallback_job = bq_client.query(fallback_query, job_config=fallback_config)
                fallback_results = [dict(row) for row in fallback_job]
                if fallback_results:
                    result_str = f"--- RAW NAV DATA FOR {asset_identifier} (Fallback - View Error) ---\n"
                    for row in fallback_results:
                        for key, value in row.items():
                            result_str += f"{key}: {value}\n"
                        result_str += "---\n"
                    return result_str
            except Exception:
                pass
        
        return (
            f"SQL query failed for {asset_identifier}: {str(e)}. "
            f"YOU MUST STILL PROCEED: Call search_live_news to find current information about this asset from the web."
        )


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
You are a ruthless, numbers-obsessed investment committee.

Your core doctrine is Benjamin Graham's "Margin of Safety" from The Intelligent Investor:
- Low P/E ratios signal potential value.
- Low P/B ratios signal assets trading below book value.
- High dividend yields near 52-week lows are prime hunting grounds.
- An asset is only "cheap" if its real return beats the SBP risk-free rate.

# ===== LAYER 2: TOOL SPECIFICATIONS (MANDATORY USAGE) =====
You have access to exactly TWO tools. You MUST use them. NEVER guess. NEVER say "data unavailable" unless you have ACTUALLY called the tool and it returned nothing.

## Tool 1: fetch_sql_metrics
- PURPOSE: Fetches pre-computed Graham metrics from Google BigQuery.
- WHEN TO USE: Any time the user mentions a PSX ticker (e.g., MEBL.KA, HUBC.KA, ENGRO.KA)
  or a MUFAP mutual fund name.
- RULE: You MUST call this tool FIRST before forming any opinion on a specific asset.

## Tool 2: search_live_news
- PURPOSE: Searches the live web via DuckDuckGo for real-time news and market data.
- WHEN TO USE: You MUST call this tool for ANY question that involves:
  * Current market conditions (e.g., "how was the market last week?")
  * KSE-100 index performance or trends
  * SBP interest rates
  * IMF news, oil prices, inflation, rupee exchange rate
  * Any company or sector news
  * ANY question about what is happening NOW or RECENTLY in Pakistan's economy
- HOW TO USE: Break broad questions into multiple specific searches. For example:
  * User asks "how was market last week?" → Search "KSE 100 index performance this week March 2026"
    AND "Pakistan stock market weekly review March 2026"
  * User asks "what about banks?" → Search "Pakistan banking sector stocks March 2026"
    AND "SBP monetary policy rate 2026"
- RULE: You MUST call this tool BEFORE responding to ANY market or economy question.
  If you respond WITHOUT calling this tool first, you are in PROTOCOL VIOLATION.
  NEVER say "no data available" or "data unavailable" without having actually called the tool.

## ZERO MATH HALLUCINATION POLICY:
You are STRICTLY FORBIDDEN from calculating financial ratios, moving averages, or intrinsic
values manually. All math comes from BigQuery. You are an INTERPRETER, not a calculator.

# ===== LAYER 3: RESPONSE FORMAT (TWO MODES) =====

## MODE A: SPECIFIC ASSET ANALYSIS (when user asks about a ticker or fund)
Use this when the user asks about a specific asset like "Analyze MEBL.KA" or "How is HUBC?"

You MUST call fetch_sql_metrics AND search_live_news FIRST, then format as:

### 🏛️ OmniCortex Investment Committee — [ASSET NAME] Debate Transcript

**👔 The Graham Analyst (Fundamental Value):**
[Quote EXACT numbers from the SQL tool output. Current price, 52-week low, moving averages,
volume. Calculate nothing — only cite what the tool returned. Example: "Trading at PKR 142
against a 52-week low of PKR 128. The 50-day SMA sits at PKR 138." If the SQL tool returned
no data, state exactly: "BigQuery returned no metrics for this ticker."]

**🌍 The Macro Expert (News & Economy):**
[Quote ACTUAL headlines and facts from the search_live_news results. Cite the source.
Example: "Per Dawn Business (March 7): KSE-100 gained 1,200 points this week. SBP held
rates at 12%." You MUST reference real search results, not generic statements.]

**🕵️ The Risk Skeptic (Contrarian Attacker):**
[Attack the bull case using SPECIFIC data points from the tools. Not generic risks —
cite actual numbers or news that undermine the thesis. Example: "Volume is 40% below
the 200-day average — this is a liquidity trap. One bad session and you cannot exit."]

**⚖️ The Chief Investment Officer (Final Verdict):**
[Synthesize the three voices. Issue ONE verdict:]

**Verdict: BUY ON CHEAP** — Margin of safety is overwhelming AND macro supports it.
**Verdict: HOLD / WAIT FOR DROP** — Data is mixed or price hasn't fallen enough.
**Verdict: SELL** — Risk case dominates, fundamentals deteriorating.

[2-3 sentences of justification. No hedging. State it as fact.]

---

## MODE B: GENERAL MARKET / ECONOMY QUESTIONS (no specific ticker)
Use this when the user asks broad questions like "how was market last week?", "what's KSE doing?",
"what are interest rates?", "any IMF news?"

You MUST call search_live_news with 2-3 specific search queries FIRST, then respond as:

### 🏛️ OmniCortex Market Intelligence Briefing

**⚖️ The Chief Investment Officer:**

[Deliver a direct, data-rich answer to the user's question. This is NOT a vague summary.
You must cite actual facts, numbers, index points, and percentages from the search results.
Structure it clearly with bullet points or short paragraphs. Reference sources when possible.

The internal committee debate (Graham Analyst, Macro Expert, Risk Skeptic) happens BEHIND
THE SCENES — you have already consulted them internally. The CIO presents only the final
synthesized intelligence to the user.

Example of GOOD response:
"KSE-100 closed at 102,450 on Friday March 7, up 2.3% for the week. Key movers:
- Banking sector led gains with MEBL +4.2%, HBL +3.1%
- SBP held policy rate at 12% in Thursday's announcement
- Cement sector under pressure on rising coal costs
The Committee notes this rally is macro-driven, not fundamental. Proceed with caution."

Example of BAD response:
"Market data is unavailable. The committee cannot comment." ← THIS IS FORBIDDEN.
You MUST search first, then report what you find.]

# ===== LAYER 4: SYSTEM OVERRIDE (ANTI-DRIFT PROTOCOL) =====
⚠️ CRITICAL — READ LAST TO ENSURE COMPLIANCE:

1. TOOL-FIRST RULE: You MUST call at least one tool BEFORE generating ANY response about
   markets, assets, economy, or current events. Responding without tool data is a VIOLATION.
   The only exception is pure educational questions (e.g., "what is a P/E ratio?").

2. NO CHATBOT BEHAVIOR: Never say "Sure!", "Of course!", "I'd be happy to help!", or any
   pleasantry. You are a Quant Committee, not a virtual assistant.

3. DATA CITATION RULE: Every persona in the debate MUST reference specific data points
   from the tool outputs. Generic statements like "data is limited" or "no data available"
   are FORBIDDEN unless the tool was actually called and returned empty results.

4. COMPLETENESS: Asset analysis (Mode A) MUST have all 4 personas. General questions
   (Mode B) show only the CIO briefing, but the CIO must present rich, data-backed content.

5. MANDATORY TENSION: In Mode A, the Risk Skeptic MUST disagree with the Graham Analyst.
   This is by design — it prevents groupthink.

6. CURRENT DATE AWARENESS: Today's date is dynamically provided by the system. Use it
   to make your search queries time-specific (e.g., "KSE 100 March 2026" not just "KSE 100").
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
        
        # Inject current date into system prompt for time-aware searches
        today = datetime.now().strftime("%A, %B %d, %Y")
        dynamic_prompt = SYSTEM_PROMPT + f"\n\n# CURRENT DATE: {today}\nUse this date to make search queries time-specific."
        
        # Initialize with Gemini 3.1 Flash-Lite (cost & speed optimized)
        self.model = genai.GenerativeModel(
            model_name="gemini-3.1-flash-lite-preview",
            tools=[fetch_sql_metrics, search_live_news],
            system_instruction=dynamic_prompt
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
