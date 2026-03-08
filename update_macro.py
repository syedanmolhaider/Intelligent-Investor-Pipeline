import os
from google.cloud import bigquery
from datetime import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"

def update_macro_indicators():
    client = bigquery.Client()
    table_id = "pk-market-data.market_data.macro_indicators"
    
    schema = [
        bigquery.SchemaField("Date", "DATE"),
        bigquery.SchemaField("SBP_Rate", "FLOAT"),
        bigquery.SchemaField("Indicator_Name", "STRING")
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    try:
        table = client.create_table(table, exists_ok=True)
        print(f"Table {table_id} ready.")
    except Exception as e:
        print(f"Error checking/creating table: {e}")
        
    # Example: Insert current SBP rate
    rows_to_insert = [
        {
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "SBP_Rate": 22.0,
            "Indicator_Name": "SBP_Policy_Rate"
        }
    ]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if not errors:
        print("Macro indicator updated successfully.")
    else:
        print(f"Encountered errors while inserting rows: {errors}")

if __name__ == "__main__":
    update_macro_indicators()
