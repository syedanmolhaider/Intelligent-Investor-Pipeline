import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

query = """
    SELECT Date, Fund_Name FROM `pk-market-data.market_data.mufap_performance_metrics`
    WHERE Fund_Name LIKE '%NBP Islamic Stock Fund%'
    ORDER BY Date DESC
    LIMIT 5
"""
results = list(client.query(query))
for r in results:
    print(r.Date, r.Fund_Name)
