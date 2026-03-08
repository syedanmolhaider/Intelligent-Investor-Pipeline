import os
from google.cloud import bigquery
from duckduckgo_search import DDGS

# ==================== STANDALONE TOOL MODULE ====================
# These are standalone versions of the tools for independent testing
# and potential future use with other frameworks.
# The primary tools used by OmniCortex are in core_brain.py.

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
bq_client = bigquery.Client()


def fetch_sql_metrics(asset_identifier: str) -> str:
    """
    Fetches pre-computed Benjamin Graham and performance metrics for a specific asset.
    Input should be the exact PSX Ticker (e.g., 'MEBL.KA' or 'HUBC.KA') or a MUFAP Fund Name.
    All math is pre-computed in BigQuery SQL Views — never guess numbers.
    """
    # Sanitize input
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
            return f"No metrics found for {asset_type} asset: {asset_identifier}. Verify the ticker/fund name."
            
        result_str = f"--- PRE-COMPUTED SQL METRICS FOR {asset_identifier} ({asset_type}) ---\n"
        for key, value in results[0].items():
            result_str += f"{key}: {value}\n"
        return result_str
        
    except Exception as e:
        return f"Database Query Failed: {str(e)}"


def search_live_news(search_query: str) -> str:
    """
    Searches the live web for real-time news, macro-economic indicators,
    and market data for the Pakistani market.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                search_query,
                region='wt-wt',
                safesearch='moderate',
                max_results=10  # 10 results per blueprint spec
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


if __name__ == "__main__":
    print("=" * 60)
    print("  OmniCortex Tool Test Suite")
    print("=" * 60)
    
    print("\n[1/2] Testing BigQuery Tool (MEBL.KA)...")
    print(fetch_sql_metrics("MEBL.KA"))
    
    print("\n[2/2] Testing Web Search Tool...")
    print(search_live_news("State Bank of Pakistan interest rate today"))
    
    print("\n[DONE] All tools operational.")
