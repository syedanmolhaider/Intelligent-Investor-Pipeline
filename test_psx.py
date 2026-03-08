import cloudscraper

s = cloudscraper.create_scraper()
r = s.get('https://dps.psx.com.pk/timeseries/intraday/KSE100')
print('timeseries:', r.status_code)
if r.status_code == 200:
    print(r.text[:500])

r2 = s.get('https://dps.psx.com.pk/api/index/KSE100')
print('API:', r2.status_code)
if r2.status_code == 200:
    print(r2.text[:500])
