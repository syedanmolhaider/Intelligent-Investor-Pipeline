import os
import pandas as pd
from google.cloud import bigquery

# 1. Authenticate with Google Cloud using your JSON key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

def fetch_psx_data(ticker_symbol):
    print(f"Fetching data from TradingView for {ticker_symbol}...")
    
    # Initialize tvDatafeed
    from tvDatafeed import TvDatafeed, Interval
    import logging
    # Suppress verbose TVDatafeed login warnings
    logging.getLogger('tvDatafeed.main').setLevel(logging.ERROR)
    
    tv = TvDatafeed()
    
    # Extract data for the last 5 days
    df = tv.get_hist(symbol=ticker_symbol, exchange='PSX', interval=Interval.in_daily, n_bars=5)
    
    if df is None or df.empty:
         raise ValueError(f"No data returned for {ticker_symbol} from TradingView PSX")
    
    # Transform: Clean up the dataframe to match our database schema
    df.reset_index(inplace=True)
    # tvDatafeed returns column format: datetime, symbol, open, high, low, close, volume
    # Our schema: Date, Close, Volume, Ticker
    df.rename(columns={'datetime': 'Date', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
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
    try:
        # Define your project.dataset.table
        # REPLACE 'pk-market-data' with your actual Google Cloud Project ID if different
        BQ_TABLE_ID = "pk-market-data.market_data.psx_daily_equities"
        
        # Run the pipeline for Meezan Bank
        meezan_data = fetch_psx_data("MEBL")
        
        # KSE100 pipeline
        kse_data = fetch_psx_data("KSE100")
        
        # Push to the database
        load_to_bigquery(meezan_data, BQ_TABLE_ID)
        load_to_bigquery(kse_data, BQ_TABLE_ID)
    except Exception as e:
        import logging
        logging.basicConfig(filename='etl_errors.log', level=logging.ERROR, format='%(asctime)s - %(message)s')
        
        error_msg = f"tvDatafeed Pipeline Failed: {str(e)}"
        print(error_msg)
        logging.error(error_msg)