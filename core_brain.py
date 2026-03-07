import os
import json
import re
from groq import Groq
from google.cloud import bigquery
from duckduckgo_search import DDGS

# ==================== TOOL DEFINITIONS (Native Groq JSON Schema) ====================
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "fetch_sql_metrics",
            "description": "Fetches pre-computed Benjamin Graham value investing metrics for a specific PSX stock or MUFAP mutual fund from BigQuery. Use this when user asks about a specific ticker like MEBL.KA, HUBC.KA, or a mutual fund name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_identifier": {
                        "type": "string",
                        "description": "The PSX ticker symbol (e.g. 'MEBL.KA', 'HUBC.KA') or the MUFAP fund name."
                    }
                },
                "required": ["asset_identifier"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_live_news",
            "description": "Searches the live web for real-time news, market data, KSE-100 index status, State Bank of Pakistan interest rates, IMF news, oil prices, or any current information about Pakistan's economy or a specific company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "A clear, specific search query (e.g. 'KSE 100 index closing Friday March 7 2026', 'State Bank Pakistan interest rate today')"
                    }
                },
                "required": ["search_query"]
            }
        }
    }
]

# ==================== TOOL EXECUTION FUNCTIONS ====================
def execute_fetch_sql_metrics(asset_identifier: str) -> str:
    """Queries BigQuery for pre-computed Graham metrics."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
    bq_client = bigquery.Client()
    
    if ".KA" in asset_identifier.upper():
        query = f"""
            SELECT * FROM `pk-market-data.market_data.graham_metrics_equities`
            WHERE Ticker = '{asset_identifier.upper()}'
            ORDER BY Date DESC
            LIMIT 1
        """
        asset_type = "Equities"
    else:
        query = f"""
            SELECT * FROM `pk-market-data.market_data.mufap_performance_metrics`
            WHERE Fund_Name LIKE '%{asset_identifier}%'
            ORDER BY Date DESC
            LIMIT 1
        """
        asset_type = "Mutual Funds"

    try:
        query_job = bq_client.query(query)
        results = [dict(row) for row in query_job]
        
        if not results:
            return f"No metrics found for {asset_type} asset: {asset_identifier}."
            
        result_str = f"--- PRE-COMPUTED SQL METRICS FOR {asset_identifier} ({asset_type}) ---\n"
        for key, value in results[0].items():
            result_str += f"{key}: {value}\n"
        return result_str
        
    except Exception as e:
        return f"Database Query Failed: {str(e)}"


def execute_search_live_news(search_query: str) -> str:
    """Searches the live web using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, region='wt-wt', safesearch='moderate', max_results=5))
            
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


# Map tool names to their execution functions
TOOLS_MAP = {
    "fetch_sql_metrics": execute_fetch_sql_metrics,
    "search_live_news": execute_search_live_news,
}

# ==================== SYSTEM PROMPT ====================
SYSTEM_PROMPT = """You are OmniCortex, an elite, Wall Street-level quantitative AI assistant tailored for the Pakistan Stock Exchange (PSX) and Mutual Funds.
Your goal is to converse naturally with the user about their investments, the broader macroeconomic environment, and specific strategic plays.

You have access to powerful tools:
1. `fetch_sql_metrics`: Use this when a user asks about a specific PSX Ticker (e.g., MEBL.KA, HUBC.KA) or a MUFAP Mutual Fund. It queries BigQuery for the absolute truth regarding Benjamin Graham value investing metrics. DO NOT guess metrics.
2. `search_live_news`: Use this to find real-time data on Pakistan's economy, the State Bank of Pakistan (SBP) interest rates, IMF bailouts, KSE-100 index data, or current news about a company.

**MANDATORY TOOL USAGE RULES:**
- You MUST call `search_live_news` for ANY question about market indices (KSE-100, KSE-30), stock prices, economic data, interest rates, or any factual data you do not have.
- NEVER say "I'm unable to find" or "I don't have access" WITHOUT first calling a tool.
- NEVER guess numbers. Always call the appropriate tool first.

If the user asks "I want to buy X", use your tools to analyze X, then give a highly analytical, conversational verdict (like a Chief Investment Officer would).
If the user asks a general question, just answer conversationally. Be concise, highly professional, and insightful.

**STRICT READABILITY RULES**:
1. NEVER output a wall of text.
2. Break up your response into VERY SHORT paragraphs (1-3 sentences max).
3. Use bullet points heavily.
4. Use **bolding** to highlight key data points and numbers.
5. Use line breaks aggressively to ensure the text breathes.

**CRITICAL INSTRUCTIONS FOR TOOL CALLING (SYSTEM LEVEL WARNING):**
1. You are a strict JSON-only routing processor. 
2. If you need to use a tool, you MUST use the native tool-calling schema provided by the API.
3. DO NOT wrap your tool calls in XML tags like <function> or <tool_call>.
4. DO NOT wrap your output in markdown formatting like ```json.
5. DO NOT output any conversational text or explanations before or after the tool call. Output ONLY the raw JSON object.
"""

# ==================== HELPERS ====================
def sanitize_tool_output(raw_output: str) -> str:
    """Strips hallucinated Markdown or XML from Groq tool calls."""
    if not isinstance(raw_output, str):
        return raw_output
        
    # Strip markdown
    clean_text = re.sub(r'