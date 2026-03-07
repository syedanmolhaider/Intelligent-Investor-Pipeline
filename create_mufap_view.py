import os
from google.cloud import bigquery

# Authenticate with Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

def create_mufap_view():
    print("Creating MUFAP Mutual Funds Performance View in BigQuery...")
    
    # Define the exact SQL query
    view_sql = """
    CREATE OR REPLACE VIEW `pk-market-data.market_data.mufap_performance_metrics` AS
    WITH sorted_data AS (
        SELECT Date, Fund_Name, Category, NAV
        FROM `pk-market-data.market_data.mufap_daily_nav`
    ),
    trailing_navs AS (
        SELECT
            a.Date,
            a.Fund_Name,
            a.Category,
            a.NAV,
            -- Get NAV exactly 7 days ago (or closest available date before that)
            COALESCE(
              (SELECT b.NAV FROM sorted_data b WHERE b.Fund_Name = a.Fund_Name AND b.Date <= DATE_SUB(a.Date, INTERVAL 7 DAY) ORDER BY b.Date DESC LIMIT 1),
              FIRST_VALUE(a.NAV) OVER (PARTITION BY a.Fund_Name ORDER BY a.Date)
            ) AS nav_7d,
            
            -- Get NAV exactly 30 days ago (or nearest)
            COALESCE(
              (SELECT b.NAV FROM sorted_data b WHERE b.Fund_Name = a.Fund_Name AND b.Date <= DATE_SUB(a.Date, INTERVAL 30 DAY) ORDER BY b.Date DESC LIMIT 1),
              FIRST_VALUE(a.NAV) OVER (PARTITION BY a.Fund_Name ORDER BY a.Date)
            ) AS nav_30d
        FROM sorted_data a
    )
    SELECT 
        Date,
        Fund_Name,
        Category,
        NAV,
        
        -- Exact Growth Metrics
        ROUND(((NAV - NULLIF(nav_7d, 0)) / NULLIF(nav_7d, 0)) * 100, 4) AS wow_growth_pct,
        ROUND(((NAV - NULLIF(nav_30d, 0)) / NULLIF(nav_30d, 0)) * 100, 4) AS mom_growth_pct,
        
        -- Extrapolating 30-day Month-over-Month growth to Annualized Growth
        ROUND((POWER(1 + ((NAV - NULLIF(nav_30d, 0)) / NULLIF(nav_30d, 0)), 12) - 1) * 100, 4) AS annualized_return_from_mom,
        
        -- The Graham Filter: Does this annualized return beat the baseline 22% SBP Risk-Free rate?
        CASE 
            WHEN ROUND((POWER(1 + ((NAV - NULLIF(nav_30d, 0)) / NULLIF(nav_30d, 0)), 12) - 1) * 100, 4) > 22.0 THEN True 
            ELSE False 
        END AS beats_sbp_22pct
        
    FROM trailing_navs
    """
    
    # Execute the query
    job = client.query(view_sql)
    job.result()  # Wait for the job to complete
    
    print("Successfully created the view `mufap_performance_metrics` via Python!")

if __name__ == "__main__":
    create_mufap_view()
