import os
from google.cloud import bigquery
from datetime import datetime, timedelta

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

def inject_historical_nav():
    table_id = "pk-market-data.market_data.mufap_daily_nav"
    
    # 7 days ago and 30 days ago
    date_7d = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    date_30d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    rows_to_insert = [
        {
            "Date": date_7d,
            "Fund_Name": "NBP Islamic Stock Fund",
            "Category": "Shariah Compliant Equity (Absolute Return )",
            "NAV": 22.75,
            "Repurchase_Price": None
        },
        {
            "Date": date_30d,
            "Fund_Name": "NBP Islamic Stock Fund",
            "Category": "Shariah Compliant Equity (Absolute Return )",
            "NAV": 22.30,
            "Repurchase_Price": None
        }
    ]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors == []:
        print(f"Successfully injected historical data for NBP Islamic Stock Fund.")
    else:
        print(f"Errors occurred while injecting data: {errors}")

if __name__ == "__main__":
    inject_historical_nav()
