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
                        "description": "A clear, specific search query (e.g. 'KSE 100 index closing Friday March 6', 'State Bank Pakistan interest rate today')"
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
            # Increased max_results to 10 to give the AI more context to extract exact numbers
            results = list(ddgs.text(search_query, region='wt-wt', safesearch='moderate', max_results=10))
            
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
SYSTEM_PROMPT = """You are the OmniCortex Master Brain, an autonomous AI investment committee for the Pakistani market (PSX & MUFAP). 

**MANDATORY TOOL USAGE:**
- If asked about an asset, you MUST call `fetch_sql_metrics`. 
- You MUST call `search_live_news` to check KSE-100 trends, SBP interest rates, or company news. 
- NEVER GUESS NUMBERS.

**CRITICAL INSTRUCTIONS FOR TOOL CALLING:**
1. You are strictly JSON-only for tool calls. DO NOT wrap tools in XML or markdown.
2. Output ONLY raw JSON when calling a tool.

**FINAL RESPONSE FORMAT (ABSOLUTELY MANDATORY):**
You DO NOT act as a standard, polite chatbot. When you have finished fetching data and are ready to reply to the user, you MUST NEVER write a basic summary like "Based on the metrics...". 
Instead, you MUST structure your final response EXACTLY as the following meeting transcript. Start the debate immediately.

### 🏛️ OmniCortex Investment Committee Debate

**👔 The Graham Analyst (Fundamental Value):**
[Evaluate the SQL metrics exactly. Is the price near the 52-week low? Are the moving averages showing a discount? Speak strictly in numbers and margins of safety.]

**🌍 The Macro Expert (News & Economy):**
[Evaluate the DuckDuckGo news, KSE-100 trends, and Pakistan's macro environment. Does the current economy support buying this asset? If no news was found, state that it lacks market visibility.]

**🕵️ The Risk Skeptic (Contrarian Attacker):**
[Ruthlessly attack the Analyst's thesis. Point out missing data, geopolitical risks, pink sheets, or why this might be a 'value trap'. Be highly pessimistic.]

**⚖️ The Chief Investment Officer (Final Verdict):**
[Synthesize the debate. Issue a clear, bolded, final verdict: **BUY ON CHEAP**, **HOLD / WAIT FOR DROP**, or **SELL**. Justify the decision strictly based on the margin of safety vs. risk.]
"""

# ==================== HELPERS ====================
def sanitize_tool_output(raw_output: str) -> str:
    """Strips hallucinated Markdown or XML from Groq tool calls."""
    if not isinstance(raw_output, str):
        return raw_output
        
    # Strip markdown - dynamically creates backticks so the Canvas parser doesn't crash!
    bt = chr(96) * 3 
    pattern = bt + r'(?:json)?\n?(.*?)\n?' + bt
    clean_text = re.sub(pattern, r'\1', raw_output, flags=re.DOTALL)
    
    # Strip DeepSeek-R1 reasoning blocks (CRITICAL FOR NEW MODEL)
    clean_text = re.sub(r'<think>\s*(.*?)\s*</think>', '', clean_text, flags=re.DOTALL)
    
    # Strip XML tags
    clean_text = re.sub(r'<function>\s*(.*?)\s*</function>', r'\1', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'<tool_call>\s*(.*?)\s*</tool_call>', r'\1', clean_text, flags=re.DOTALL)
    
    return clean_text.strip()


# ==================== OMNICORTEX BRAIN (Native Groq SDK) ====================
class OmniCortexBrain:
    """
    The OmniCortex Master Brain using Groq's NATIVE Python SDK.
    Bypasses all LangChain/LangGraph wrappers to eliminate tool-calling bugs.
    """

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not found.")
        
        self.client = Groq(api_key=api_key)
        # UPGRADED TO DEEPSEEK-R1 (Smartest reasoning model currently on Groq)
        self.model = "deepseek-r1-distill-llama-70b"

    def invoke(self, messages_input: dict) -> dict:
        messages = []
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
        
        for msg in messages_input.get("messages", []):
            if hasattr(msg, 'content'):
                if hasattr(msg, 'type'):
                    role = "user" if msg.type == "human" else "assistant"
                else:
                    role = getattr(msg, 'role', 'user')
                messages.append({"role": role, "content": msg.content})
            elif isinstance(msg, dict):
                messages.append(msg)

        # Tool-calling loop (max 5 iterations)
        for iteration in range(5):
            print(f"[OmniCortex] Iteration {iteration + 1}: Sending {len(messages)} messages to Groq...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.0,
                max_tokens=4096,
            )
            
            response_message = response.choices[0].message
            
            # If no tool calls, we're done
            if not response_message.tool_calls:
                print(f"[OmniCortex] No tool calls. Final response length: {len(response_message.content or '')} chars")
                final_content = response_message.content or "I apologize, I was unable to generate a response."
                
                class FakeMessage:
                    def __init__(self, content):
                        self.content = content
                
                return {"messages": messages_input.get("messages", []) + [FakeMessage(final_content)]}

            print(f"[OmniCortex] Tool calls detected: {[tc.function.name for tc in response_message.tool_calls]}")
            
            # --- CRITICAL FIX: SANITIZE TOOL CALLS BEFORE APPENDING TO HISTORY ---
            sanitized_tool_calls = []
            for tc in response_message.tool_calls:
                clean_args = sanitize_tool_output(tc.function.arguments)
                sanitized_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": clean_args
                    }
                })

            # Append the assistant's response (with cleaned tool calls) to messages
            messages.append({
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": sanitized_tool_calls
            })

            # Execute each tool and append results
            for tc_dict in sanitized_tool_calls:
                tool_name = tc_dict["function"]["name"]
                raw_args = tc_dict["function"]["arguments"]
                
                try:
                    # Will safely parse now that XML is stripped
                    tool_args = json.loads(raw_args)
                    print(f"[OmniCortex] Executing: {tool_name}({tool_args})")
                    
                    if tool_name in TOOLS_MAP:
                        result = TOOLS_MAP[tool_name](**tool_args)
                        print(f"[OmniCortex] Tool result preview: {str(result)[:200]}...")
                    else:
                        result = f"Unknown tool: {tool_name}"
                        
                except json.JSONDecodeError as e:
                    # Stops the app from crashing entirely if the AI fails completely
                    result = f"Error: You generated invalid JSON for the tool call. Fix your formatting. Details: {str(e)}"
                    print(f"[OmniCortex] JSON Parse ERROR: {e}")
                except Exception as e:
                    result = f"Tool execution error: {str(e)}"
                    print(f"[OmniCortex] Tool ERROR: {e}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_dict["id"],
                    "content": str(result)
                })

        # Fallback if loop runs out
        class FakeMessage:
            def __init__(self, content):
                self.content = content
        return {"messages": messages_input.get("messages", []) + [FakeMessage("Analysis complete. Please ask a follow-up question.")]}


def get_omnicortex_brain():
    """Factory function that returns the OmniCortex brain instance."""
    return OmniCortexBrain()