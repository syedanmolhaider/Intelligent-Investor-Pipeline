import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

query = """
    SELECT DISTINCT Fund_Name FROM `pk-market-data.market_data.mufap_performance_metrics`
    WHERE Fund_Name LIKE '%NBP%'
"""
results = list(client.query(query))
for r in results:
    print(r.Fund_Name)
