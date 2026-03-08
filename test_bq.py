import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"
from google.cloud import bigquery
bq = bigquery.Client()

# Test 1: Does the view exist?
print("=== Test 1: Check if mufap view exists ===")
try:
    q = bq.query("SELECT * FROM `pk-market-data.market_data.mufap_performance_metrics` LIMIT 1")
    rows = [dict(r) for r in q]
    if rows:
        print("View exists. Columns:", list(rows[0].keys()))
        print("Sample:", rows[0])
    else:
        print("View exists but is EMPTY.")
except Exception as e:
    print(f"VIEW ERROR: {e}")

# Test 2: Parameterized LIKE query (same as core_brain.py uses)
print("\n=== Test 2: Parameterized LIKE query for NBP ===")
try:
    query = """
        SELECT Fund_Name, NAV, Date
        FROM `pk-market-data.market_data.mufap_performance_metrics`
        WHERE Fund_Name LIKE CONCAT('%', @fund_name, '%')
        ORDER BY Date DESC
        LIMIT 3
    """
    jc = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("fund_name", "STRING", "NBP")]
    )
    rows = [dict(r) for r in bq.query(query, job_config=jc)]
    print(f"Found {len(rows)} results")
    for r in rows:
        print(r)
except Exception as e:
    print(f"PARAM QUERY ERROR: {e}")

# Test 3: What fund names contain 'NBP'?
print("\n=== Test 3: Direct search for NBP fund names ===")
try:
    q = bq.query("""
        SELECT DISTINCT Fund_Name
        FROM `pk-market-data.market_data.mufap_daily_nav`
        WHERE Fund_Name LIKE '%NBP%'
        LIMIT 10
    """)
    rows = [dict(r) for r in q]
    print(f"Found {len(rows)} distinct fund names with 'NBP':")
    for r in rows:
        print(f"  - {r['Fund_Name']}")
except Exception as e:
    print(f"DIRECT QUERY ERROR: {e}")

# Test 4: Sample of all fund names
print("\n=== Test 4: Sample fund names from raw table ===")
try:
    q = bq.query("""
        SELECT DISTINCT Fund_Name
        FROM `pk-market-data.market_data.mufap_daily_nav`
        LIMIT 15
    """)
    rows = [dict(r) for r in q]
    print(f"Sample of {len(rows)} fund names:")
    for r in rows:
        print(f"  - {r['Fund_Name']}")
except Exception as e:
    print(f"SAMPLE ERROR: {e}")
