import os
import pandas as pd
import yfinance as yf
from google.cloud import bigquery

# 1. Authenticate with Google Cloud using your JSON key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

def fetch_psx_data(ticker_symbol):
    print(f"Fetching data for {ticker_symbol}...")
    # Extract data for the last 5 days
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="5d")
    
    # Transform: Clean up the dataframe to match our database schema
    df.reset_index(inplace=True)
    df = df[['Date', 'Close', 'Volume']]
    df['Ticker'] = ticker_symbol
    # Ensure Date is timezone-naive so BigQuery accepts it easily
    df['Date'] = df['Date'].dt.tz_localize(None) 
    
    return df

def load_to_bigquery(dataframe, table_id):
    print(f"Loading data to BigQuery table: {table_id}...")
    
    # Load: Configure the job to append new data to the table
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
    )
    
    job = client.load_table_from_dataframe(
        dataframe, table_id, job_config=job_config
    )
    job.result() # Wait for the job to complete
    print(f"Successfully loaded {len(dataframe)} rows to BigQuery.")

if __name__ == "__main__":
    # Define your project.dataset.table
    # REPLACE 'pk-market-data' with your actual Google Cloud Project ID if different
    BQ_TABLE_ID = "pk-market-data.market_data.psx_daily_equities"
    
    # Run the pipeline for Meezan Bank (MEBL.KA is the Yahoo Finance ticker for it)
    meezan_data = fetch_psx_data("MEBL.KA")
    
    # Push to the database
    load_to_bigquery(meezan_data, BQ_TABLE_ID)