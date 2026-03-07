import os
import pandas as pd
import cloudscraper
from datetime import datetime
from google.cloud import bigquery
from io import StringIO

# Authenticate with Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

def fetch_mufap_data():
    print("Fetching live mutual fund data from the new MUFAP portal...")
    
    url = "https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=1"
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    response = scraper.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch. Status code: {response.status_code}")
        return None

    html_data = StringIO(response.text)
    
    try:
        tables = pd.read_html(html_data)
        df = tables[0] # The new site puts everything neatly in the very first table
    except ValueError:
        print("Error: Could not find data tables.")
        return None
        
    # Transform: Rename the exact columns we found in our debug test
    df = df.rename(columns={
        "Fund Name": "Fund_Name"
    })
    
    # Add today's date
    df["Date"] = pd.to_datetime(datetime.today().date())
    
    # Create an empty Repurchase_Price column to satisfy our BigQuery schema
    df["Repurchase_Price"] = None
    
    # Filter down to just our 5 required columns
    expected_cols = ["Date", "Fund_Name", "Category", "NAV", "Repurchase_Price"]
    df = df[expected_cols]
    
    # Remove empty rows or sub-headers disguised as data
    df = df.dropna(subset=["Fund_Name", "NAV"])
    
    # Force NAV into a clean decimal number
    df['NAV'] = pd.to_numeric(df['NAV'], errors='coerce')
    
    # Final clean: Drop any rows where NAV failed to become a number
    df = df.dropna(subset=["NAV"])
    
    return df

def load_to_bigquery(dataframe, table_id):
    if dataframe is None or dataframe.empty:
        print("No data to load today.")
        return
        
    print(f"Loading data to BigQuery table: {table_id}...")
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    job = client.load_table_from_dataframe(dataframe, table_id, job_config=job_config)
    job.result() 
    print(f"Successfully loaded {len(dataframe)} rows to BigQuery.")

if __name__ == "__main__":
    BQ_TABLE_ID = "pk-market-data.market_data.mufap_daily_nav"
    mufap_df = fetch_mufap_data()
    load_to_bigquery(mufap_df, BQ_TABLE_ID)