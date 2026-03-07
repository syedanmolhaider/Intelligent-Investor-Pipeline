import cloudscraper
import pandas as pd
from io import StringIO

def inspect_mufap():
    print("Fetching the NEW MUFAP website to inspect table structures...")
    
    # Target the new daily industry statistics page
    url = "https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=1"
    
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    response = scraper.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return
        
    html_data = StringIO(response.text)
    
    try:
        tables = pd.read_html(html_data)
        print(f"\nSuccess! Found {len(tables)} tables on the new page.\n")
    except ValueError:
        print("No tables found. They might be rendering the data with JavaScript now.")
        return

    # Print the columns of the first few tables so we can see their exact names
    for i, t in enumerate(tables[:3]): 
        print(f"--- Table {i+1} ---")
        
        # Flatten headers if they are multi-level
        if isinstance(t.columns, pd.MultiIndex):
            cols = list(t.columns.get_level_values(-1))
        else:
            cols = list(t.columns)
            
        print(f"Columns: {cols}")
        print(f"First row sample: {t.head(1).values.tolist()}\n")

if __name__ == "__main__":
    inspect_mufap()