import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging


def fetch_zillow_details(query):
    """
    Fetch property details from Zillow given an address or Zillow URL.
    If query is an address, perform a Zillow search and use the first result.
    Returns a dictionary with keys: address, price, beds, baths, sqft, year_built, image_url, etc.
    If no data is found, returns None. Raises on network or parsing errors.
    """
    if not query:
        return None
    # More realistic browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        # 'Cookie': '',  # Optionally set cookies if needed
    }
    # If not a URL, search Zillow for the address
    if not query.startswith('http'):
        search_url = f"https://www.zillow.com/homes/{urllib.parse.quote(query)}/"
        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Zillow search results are often in <a> tags with hrefs to property pages
            # Try to find the first property link
            link = None
            for a in soup.find_all('a', href=True):
                href = a['href']
                if re.match(r"^/homedetails/", href):
                    link = href
                    break
            if not link:
                raise ValueError('No property found for the given address.')
            # Construct full URL if needed
            if link.startswith('/'):
                property_url = f"https://www.zillow.com{link}"
            else:
                property_url = link
        except Exception as e:
            raise RuntimeError(f'Failed to search Zillow: {e}')
    else:
        property_url = query
    # Now fetch the property details page
    try:
        resp = requests.get(property_url, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text
        logging.warning(f"Fetched Zillow HTML length: {len(html)}")
        logging.warning(f"Fetched Zillow HTML snippet: {html[:500]}")
        soup = BeautifulSoup(html, 'html.parser')
        # Placeholder parsing logic
        address = soup.find('h1', {'data-testid': 'home-details-summary-headline'})
        price = soup.find('span', {'data-testid': 'price'})
        if not address and not price:
            raise RuntimeError('Could not find property details. The page may be bot-protected or the structure has changed.')
        address = address.get_text(strip=True) if address else None
        price = price.get_text(strip=True) if price else None
        beds = baths = sqft = year_built = image_url = None
        summary = soup.find('ul', {'class': re.compile(r'.*ds-home-fact-list.*')})
        if summary:
            items = summary.find_all('li')
            for item in items:
                text = item.get_text()
                if 'bd' in text:
                    beds = text.split('bd')[0].strip()
                elif 'ba' in text:
                    baths = text.split('ba')[0].strip()
                elif 'sqft' in text:
                    sqft = text.split('sqft')[0].strip()
        facts = soup.find_all('span', string=re.compile(r'Year built'))
        if facts:
            for fact in facts:
                parent = fact.find_parent('li')
                if parent:
                    year_built = parent.get_text().split(':')[-1].strip()
        img_tag = soup.find('img', {'data-testid': 'hero-image'})
        if img_tag:
            image_url = img_tag.get('src')
        return {
            'address': address,
            'price': price,
            'beds': beds,
            'baths': baths,
            'sqft': sqft,
            'year_built': year_built,
            'image_url': image_url,
        }
    except Exception as e:
        raise RuntimeError(f'Failed to fetch Zillow details: {e}') 