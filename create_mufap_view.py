import os
from google.cloud import bigquery

# Authenticate with Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
client = bigquery.Client()

def create_mufap_view():
    print("Recreating MUFAP Performance View (without correlated subqueries)...")
    
    # Rewritten to use JOINs instead of correlated subqueries
    # BigQuery does not support correlated subqueries referencing other tables
    view_sql = """
    CREATE OR REPLACE VIEW `pk-market-data.market_data.mufap_performance_metrics` AS
    WITH ranked_data AS (
        SELECT 
            Date, 
            Fund_Name, 
            Category, 
            NAV,
            ROW_NUMBER() OVER (PARTITION BY Fund_Name ORDER BY Date DESC) AS rn
        FROM `pk-market-data.market_data.mufap_daily_nav`
        WHERE NAV IS NOT NULL AND NAV > 0
    ),
    latest AS (
        -- Get the most recent record for each fund
        SELECT * FROM ranked_data WHERE rn = 1
    ),
    nav_7d AS (
        -- Get the closest NAV from ~7 days ago
        SELECT 
            a.Fund_Name,
            b.NAV AS nav_7d_value
        FROM latest a
        LEFT JOIN (
            SELECT Fund_Name, NAV, Date,
                   ROW_NUMBER() OVER (PARTITION BY Fund_Name ORDER BY Date DESC) AS rn
            FROM `pk-market-data.market_data.mufap_daily_nav`
            WHERE NAV IS NOT NULL AND NAV > 0
              AND Date <= DATE_SUB(CURRENT_DATE(), INTERVAL 6 DAY)
        ) b ON a.Fund_Name = b.Fund_Name AND b.rn = 1
    ),
    nav_30d AS (
        -- Get the closest NAV from ~30 days ago
        SELECT 
            a.Fund_Name,
            b.NAV AS nav_30d_value
        FROM latest a
        LEFT JOIN (
            SELECT Fund_Name, NAV, Date,
                   ROW_NUMBER() OVER (PARTITION BY Fund_Name ORDER BY Date DESC) AS rn
            FROM `pk-market-data.market_data.mufap_daily_nav`
            WHERE NAV IS NOT NULL AND NAV > 0
              AND Date <= DATE_SUB(CURRENT_DATE(), INTERVAL 29 DAY)
        ) b ON a.Fund_Name = b.Fund_Name AND b.rn = 1
    ),
    macro AS (
        SELECT SBP_Rate 
        FROM `pk-market-data.market_data.macro_indicators` 
        WHERE Indicator_Name = 'SBP_Policy_Rate'
        ORDER BY Date DESC 
        LIMIT 1
    )
    SELECT 
        l.Date,
        l.Fund_Name,
        l.Category,
        l.NAV,
        
        -- Week-over-Week Growth
        ROUND(((l.NAV - NULLIF(w.nav_7d_value, 0)) / NULLIF(w.nav_7d_value, 0)) * 100, 4) AS wow_growth_pct,
        
        -- Month-over-Month Growth  
        ROUND(((l.NAV - NULLIF(m.nav_30d_value, 0)) / NULLIF(m.nav_30d_value, 0)) * 100, 4) AS mom_growth_pct,
        
        -- Annualized Return (from 30-day growth)
        ROUND((POWER(1 + ((l.NAV - NULLIF(m.nav_30d_value, 0)) / NULLIF(m.nav_30d_value, 0)), 12) - 1) * 100, 4) AS annualized_return_from_mom,
        
        -- Graham Filter: Does annualized return beat SBP Risk-Free rate?
        CASE 
            WHEN ROUND((POWER(1 + ((l.NAV - NULLIF(m.nav_30d_value, 0)) / NULLIF(m.nav_30d_value, 0)), 12) - 1) * 100, 4) > (SELECT SBP_Rate FROM macro) THEN True 
            ELSE False 
        END AS beats_sbp_rate
        
    FROM latest l
    LEFT JOIN nav_7d w ON l.Fund_Name = w.Fund_Name
    LEFT JOIN nav_30d m ON l.Fund_Name = m.Fund_Name
    CROSS JOIN macro
    """
    
    try:
        job = client.query(view_sql)
        job.result()
        print("Successfully recreated `mufap_performance_metrics` view!")
        
        # Verify it works
        test = client.query("SELECT COUNT(*) as cnt FROM `pk-market-data.market_data.mufap_performance_metrics`")
        for row in test:
            print(f"View now contains {row['cnt']} rows.")
            
    except Exception as e:
        print(f"Failed to create view: {e}")

if __name__ == "__main__":
    create_mufap_view()
