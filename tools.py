import os
from google.cloud import bigquery
from langchain.tools import tool
from duckduckgo_search import DDGS

# Ensure BigQuery matches the required auth
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
bq_client = bigquery.Client()

@tool
def fetch_sql_metrics(asset_identifier: str) -> str:
    """
    Useful for fetching pre-computed Benjamin Graham and performance metrics for a specific asset.
    Input should be the exact PSX Ticker (e.g., 'MEBL.KA' or 'HUBC.KA') or a MUFAP Fund Name.
    Do NOT guess the math yourself; use this tool to ask BigQuery for the absolute truth.
    """
    
    # Check if it looks like a Ticker (.KA usually indicates Karachi Stock Exchange on Yahoo Finance)
    if ".KA" in asset_identifier.upper():
        query = f"""
            SELECT * 
            FROM `pk-market-data.market_data.graham_metrics_equities`
            WHERE Ticker = '{asset_identifier.upper()}'
            ORDER BY Date DESC
            LIMIT 1
        """
        asset_type = "Equities"
    else:
        # Assume it's a mutual fund
        query = f"""
            SELECT * 
            FROM `pk-market-data.market_data.mufap_performance_metrics`
            WHERE Fund_Name LIKE '%{asset_identifier}%'
            ORDER BY Date DESC
            LIMIT 1
        """
        asset_type = "Mutual Funds"

    try:
        query_job = bq_client.query(query)
        results = [dict(row) for row in query_job]
        
        if not results:
            return f"No metrics found for {asset_type} asset: {asset_identifier}. Are you sure it's correct?"
            
        # Convert the dictionary output into a clean string for the LLM to read
        result_str = f"--- PRE-COMPUTED SQL METRICS FOR {asset_identifier} ({asset_type}) ---\n"
        for key, value in results[0].items():
            result_str += f"{key}: {value}\n"
        
        return result_str
        
    except Exception as e:
        return f"Database Query Failed: {str(e)}"

@tool
def search_live_news(search_query: str) -> str:
    """
    Useful for finding LIVE news, global oil prices, or Pakistani macro-economic indicators (like State Bank of Pakistan interest rates, IMF bailouts).
    Input should be a clear, specific search query (e.g., 'State Bank of Pakistan interest rate current', 'Meezan Bank latest news').
    """
    try:
        with DDGS() as ddgs:
            # Fetch top 5 news articles
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

if __name__ == "__main__":
    # Test script locally
    print("Testing BigQuery Tool...")
    print(fetch_sql_metrics("MEBL.KA"))
    
    print("\nTesting Web Search Tool...")
    print(search_live_news("State Bank of Pakistan interest rate today"))
