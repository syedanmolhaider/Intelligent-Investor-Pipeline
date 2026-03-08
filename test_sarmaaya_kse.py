import cloudscraper
from bs4 import BeautifulSoup

s = cloudscraper.create_scraper()
r = s.get('https://sarmaaya.pk/indexes/KSE100')

soup = BeautifulSoup(r.text, 'html.parser')
# Print meta tags or span with price
print(soup.title.text)

# Let's find the current price. It usually has some distinct class or ID.
for span in soup.find_all('span'):
    if '102,' in span.text or '103,' in span.text or '101,' in span.text:
        print("Found price in span:", span.text)
        print("Classes:", span.get('class'))

# Let's look for any tables for mutual funds on capital stake or other sites
r2 = s.get('https://www.psx.com.pk/')
soup2 = BeautifulSoup(r2.text, 'html.parser')
for div in soup2.find_all('div', class_='stats_item'):
    print(div.text.strip())

