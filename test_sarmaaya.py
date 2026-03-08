import cloudscraper
from bs4 import BeautifulSoup
import json

s = cloudscraper.create_scraper()
r = s.get('https://sarmaaya.pk/mutual-funds/')

soup = BeautifulSoup(r.text, 'html.parser')
for script in soup.find_all('script'):
    if script.string and 'funds' in script.string.lower():
        print("Found script containing funds:")
        print(script.string[:500])
        print("---")

print("\nTesting DPS PSX Data...")
# Often dps.psx.com.pk has a market overview API
# https://dps.psx.com.pk/historical
psx_res = s.get('https://dps.psx.com.pk/api/index/KSE100/summary')
print('PSX DPS KSE100 Summary Status:', psx_res.status_code)
if psx_res.status_code == 200:
    print(psx_res.json())

