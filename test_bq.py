import requests
import pandas as pd
from io import StringIO

url = "https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=1"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.mufap.com.pk/',
}

print(f"Testing direct requests... {url}")
try:
    r = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        tables = pd.read_html(StringIO(r.text))
        print(f"Tables: {len(tables)}")
        if tables:
            print(tables[0].head(2))
except Exception as e:
    print(f"requests failed: {e}")

url_notab = "https://www.mufap.com.pk/Industry/IndustryStatDaily"
print(f"\nTesting direct requests... {url_notab}")
try:
    r = requests.get(url_notab, headers=headers, timeout=15)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        tables = pd.read_html(StringIO(r.text))
        print(f"Tables: {len(tables)}")
        if tables:
            print(tables[0].columns.tolist())
except Exception as e:
    print(f"requests failed: {e}")
