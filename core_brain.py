import os
import json
import re
from datetime import datetime, timezone
import google.generativeai as genai
from google.cloud import bigquery
from duckduckgo_search import DDGS
import typing_extensions

class FinalVerdict(typing_extensions.TypedDict):
    graham_analysis: str
    macro_analysis: str
    risk_assessment: str
    verdict: str
    confidence_score: int

def fetch_sql_metrics(asset_identifier: str) -> str:
    """
    Fetches pre-computed Benjamin Graham value investing metrics for a specific PSX stock
    or MUFAP mutual fund from BigQuery.
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
    bq_client = bigquery.Client()
    
    safe_id = asset_identifier.replace("'", "").replace('"', '').replace(';', '').strip()
    
    # Common Acronym Mapping for MUFAP Funds (Retail Dictionary)
    acronym_map = {
        "nbpisf": "NBP Islamic Stock Fund",
        "mifl": "Meezan Islamic Fund",
        "mef": "Meezan Energy Fund",
        "agipf": "Al Ameen Shariah Stock Fund",
        "assf": "Al Ameen Shariah Stock Fund",
        "hblif": "HBL Islamic Stock Fund",
        "nitief": "NIT Islamic Equity Fund",
        "alhamra": "Alhamra Islamic Stock Fund",
        "mmsf": "Meezan Mahana Amdani Fund",
    }
    
    # Attempt to resolve common abbreviations from dirty inputs
    extracted_search = safe_id.lower().replace(" ", "")
    for ticker, full_name in acronym_map.items():
        if ticker in extracted_search:
            safe_id = full_name
            break
    
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

        def check_staleness(rows):
            if not rows:
                return False
            row_date = rows[0].get('Date')
            if not row_date:
                return False
            
            from datetime import date, datetime, timezone
            if isinstance(row_date, datetime):
                dt = row_date.astimezone(timezone.utc).replace(tzinfo=None)
            elif isinstance(row_date, date):
                dt = datetime.combine(row_date, datetime.min.time())
            elif isinstance(row_date, str):
                try:
                    dt = datetime.strptime(row_date, "%Y-%m-%d")
                except:
                    return False
            else:
                return False
            
            delta = datetime.now() - dt
            if delta.total_seconds() > 48 * 3600:
                return True
            return False

        if not results:
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
                    if check_staleness(fallback_results):
                        return "ERROR: DATA STALE. ABORT ANALYSIS."
                    result_str = f"--- RAW NAV DATA FOR {asset_identifier} (Mutual Funds - Fallback) ---\n"
                    for row in fallback_results:
                        for key, value in row.items():
                            result_str += f"{key}: {value}\n"
                        result_str += "---\n"
                    return result_str
            
            return f"No SQL metrics found for {asset_type} asset: {asset_identifier}."
            
        if check_staleness(results):
            return "ERROR: DATA STALE. ABORT ANALYSIS."

        result_str = f"--- PRE-COMPUTED SQL METRICS FOR {asset_identifier} ({asset_type}) ---\n"
        for key, value in results[0].items():
            result_str += f"{key}: {value}\n"
        return result_str
        
    except Exception as e:
        return f"SQL query failed for {asset_identifier}: {str(e)}."


def search_live_news(search_query: str) -> str:
    """
    Searches the live web for real-time news, macroeconomic data, KSE-100 trends, etc.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                search_query,
                region='wt-wt',
                safesearch='moderate',
                max_results=10
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

class OmniCortexBrain:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found.")
        
        genai.configure(api_key=api_key)
        self.today = datetime.now().strftime("%A, %B %d, %Y")
        self.model_name = "gemini-2.5-flash"
        print("[OmniCortex] Multi-Agent Sequential Pipeline Initialized.")

    def invoke(self, messages_input: dict) -> dict:
        messages = messages_input.get("messages", [])
        if not messages:
            return {"messages": [FakeMessage("No input provided.")]}

        # Extract user input
        latest_msg = messages[-1]
        raw_user_input = latest_msg.content if hasattr(latest_msg, 'content') else latest_msg.get("content", "")
        user_input = re.sub(r'\s*\(.*?\)', '', raw_user_input).strip()
        
        try:
            # =========================================================================
            # AGENT 1: GRAHAM (FUNDAMENTAL ANALYSIS)
            # =========================================================================
            print("[OmniCortex] Triggering Agent 1 (Graham)...")
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
                model_name=self.model_name,
                tools=[fetch_sql_metrics]
            )
            chat1 = graham_model.start_chat(enable_automatic_function_calling=True)
            resp1 = chat1.send_message(graham_prompt)
            graham_output = resp1.text

            # =========================================================================
            # AGENT 2: MACRO (MACROECONOMIC ANALYSIS)
            # =========================================================================
            print("[OmniCortex] Triggering Agent 2 (Macro)...")
            macro_prompt = f"""
            You are the Macroeconomic Analyst. Your ONLY tool is search_live_news.
            You must use search_live_news to fetch live macroeconomic updates, interest rates, or market news relevant to the user's query: '{user_input}'.
            Today's Date: {self.today}.
            Return a purely data-driven macroeconomic analysis. Do not include conversational filler.
            
            TRANSLATION RULE: You MUST write your analysis entirely in layman's Roman Urdu. 
            Explain macroeconomic concepts simply (e.g. explain interest rates as "bank ke munafe ki sharah", inflation as "mehengai").
            
            FORMATTING RULES:
            1. NO FLUFF: Do not use greetings or conversational filler. Start analysis immediately.
            2. BULLET POINTS: Format output strictly using short bullet points (*).
            3. WORD LIMIT: Your entire response must not exceed 40 words.
            """
            macro_model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=[search_live_news]
            )
            chat2 = macro_model.start_chat(enable_automatic_function_calling=True)
            resp2 = chat2.send_message(macro_prompt)
            macro_output = resp2.text

            # =========================================================================
            # AGENT 3: RISK (LIQUIDITY TRAPS & BLIND SPOTS)
            # =========================================================================
            print("[OmniCortex] Triggering Agent 3 (Risk)...")
            risk_prompt = f"""
            You are the Risk Analyst. Your job is to identify blind spots, liquidity traps, or risks based ONLY on the following analyses.
            Do not use tools. Identify vulnerabilities and downside risks.
            
            TRANSLATION RULE: You MUST write your analysis entirely in layman's Roman Urdu. 
            Explain risk simply (e.g. use "nuqsan ka khatra" or "paisa phansne ka dar").
            
            FORMATTING RULES:
            1. NO FLUFF: Do not use greetings or conversational filler. Start analysis immediately.
            2. BULLET POINTS: Format output strictly using short bullet points (*).
            3. WORD LIMIT: Your entire response must not exceed 40 words.
            
            ANTI-YAPPING RULE (GRACEFUL FAILURE): If Agent 1 or Agent 2 report missing data or lack of information, YOU MUST NOT write an essay about the risks of missing data. You must output exactly one sentence: 'Data dastiyab nahi. Barae meharbani durust fund ya stock ka naam likhein.' Do not elaborate further.
            
            Graham Analysis: {graham_output}
            Macro Analysis: {macro_output}
            """
            risk_model = genai.GenerativeModel(model_name=self.model_name)
            resp3 = risk_model.generate_content(risk_prompt)
            risk_output = resp3.text

            # =========================================================================
            # AGENT 4: CIO (FINAL VERDICT SYNTHESIS)
            # =========================================================================
            print("[OmniCortex] Triggering Agent 4 (CIO)...")
            cio_prompt = f"""
            You are the Chief Investment Officer. Synthesize the provided data into a final decision. 
            Do not use conversational filler. Your output must strictly adhere to the requested JSON structure.
            Your verdict must be exactly one of: 'BUY', 'HOLD', or 'SELL'.
            
            CRITICAL RULE (ANTI-YAPPING): If Agent 1 (The Graham Analyst) reports that BigQuery returned zero metrics, or that fundamental data is missing, you must immediately halt the analysis. Your final verdict key MUST strictly be 'ERROR / INSUFFICIENT DATA'. 
            In the analysis text sections, you must output exactly: 'Data dastiyab nahi. Barae meharbani durust fund ya stock ka naam likhein.' You are explicitly forbidden from issuing a BUY, HOLD, or SELL rating, and you must not speculate on why the data is missing.
            
            TRANSLATION RULE: You MUST write the string values for `graham_analysis`, `macro_analysis`, and `risk_assessment` strictly in layman's Roman Urdu. 
            However, the JSON FORMAT KEYS completely remain in exactly English (e.g. "graham_analysis", "macro_analysis"). The value for the `verdict` key MUST also remain strictly in standard English (BUY / HOLD / SELL / ERROR / INSUFFICIENT DATA).
            
            FORMATTING RULES:
            1. NO FLUFF: Do not use greetings. Start analysis immediately.
            2. BULLET POINTS: Output the Roman Urdu text within the JSON values formatted with short bullet points (*).
            3. WORD LIMIT: No text section (graham_analysis, macro_analysis, risk_assessment) can exceed 40 words.
            4. MARKDOWN BOLDING: Format the Roman Urdu output inside the JSON payload using Markdown bolding (**text**) and line breaks (\\n) so it renders cleanly and is easy to scan.
            
            Graham Analysis: {graham_output}
            Macro Analysis: {macro_output}
            Risk Assessment: {risk_output}
            """
            cio_model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": FinalVerdict
                }
            )
            resp4 = cio_model.generate_content(cio_prompt)
            
            # The resp4.text is guaranteed to be JSON matching FinalVerdict
            final_content = resp4.text
            print(f"[OmniCortex] Sequential Pipeline Complete. Response Length: {len(final_content)}")

        except Exception as e:
            print(f"[OmniCortex] CRITICAL ERROR: {str(e)}")
            error_data = {
                "graham_analysis": "Error in pipeline.",
                "macro_analysis": "Error in pipeline.",
                "risk_assessment": f"System Failure: {str(e)}",
                "verdict": "ERROR",
                "confidence_score": 0
            }
            final_content = json.dumps(error_data)

        return {"messages": messages + [FakeMessage(final_content)]}

class FakeMessage:
    def __init__(self, content):
        self.content = content
        self.type = "ai"

def get_omnicortex_brain():
    return OmniCortexBrain()
