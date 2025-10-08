"""
Enhanced Zillow Property Scraper - 2025 Edition
Implements modern anti-bot detection bypass using Playwright + ScraperAPI
Handles 403 Forbidden errors and provides reliable property data extraction
"""

import asyncio
import json
import logging
import os
import random
import re
import time
import urllib.parse
from typing import Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup

# Import Playwright with error handling for optional dependency
try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. Install with: pip install playwright playwright-stealth")

# Import undetected-chromedriver as fallback
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available. Install with: pip install undetected-chromedriver selenium")


class ZillowScraperV2:
    """
    Advanced Zillow scraper with multiple bypass strategies.
    
    Features:
    - Playwright with stealth patches (primary method)
    - ScraperAPI integration (reliable fallback)
    - Undetected Chrome (selenium fallback) 
    - Human behavior simulation
    - Rate limiting and retry logic
    - Comprehensive error handling
    """
    
    def __init__(self, scraperapi_key: Optional[str] = None, headless: bool = True):
        self.scraperapi_key = scraperapi_key or os.getenv('SCRAPERAPI_KEY')
        self.headless = headless
        self.session = requests.Session()
        
        # Enhanced headers rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
        ]
        
        self.setup_session()
    
    def setup_session(self):
        """Configure session with realistic headers."""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'Cache-Control': 'max-age=0'
        })
    
    def get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers to avoid detection."""
        headers = self.session.headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        return headers
    
    def extract_zpid_from_url(self, url: str) -> Optional[str]:
        """Extract Zillow Property ID from URL for API calls."""
        zpid_match = re.search(r'(\d+)_zpid', url)
        return zpid_match.group(1) if zpid_match else None
    
    def search_property_url(self, address: str) -> Optional[str]:
        """Search Zillow for property URL using multiple strategies."""
        strategies = [
            self._search_with_scraperapi,
            self._search_with_playwright,
            self._search_with_requests
        ]
        
        for strategy in strategies:
            try:
                result = strategy(address)
                if result:
                    return result
            except Exception as e:
                logging.warning(f"Search strategy {strategy.__name__} failed: {e}")
                continue
        
        return None
    
    def _search_with_scraperapi(self, address: str) -> Optional[str]:
        """Search using ScraperAPI for reliability."""
        if not self.scraperapi_key:
            return None
            
        search_url = f"https://www.zillow.com/homes/{urllib.parse.quote(address)}/"
        payload = {
            'api_key': self.scraperapi_key,
            'url': search_url,
            'render': 'true',
            'country_code': 'us'
        }
        
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        return self._find_property_link(soup)
    
    def _search_with_playwright(self, address: str) -> Optional[str]:
        """Search using Playwright with stealth patches."""
        if not PLAYWRIGHT_AVAILABLE:
            return None
            
        search_url = f"https://www.zillow.com/homes/{urllib.parse.quote(address)}/"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            context = browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1366, 'height': 768},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            
            # Human-like navigation
            # Use faster load strategy for search
            try:
                page.goto(search_url, wait_until='load', timeout=15000)
                page.wait_for_timeout(2000)
            except Exception:
                page.goto(search_url, wait_until='domcontentloaded', timeout=10000)
            page.wait_for_timeout(random.randint(2000, 5000))
            
            # Sometimes Zillow shows a popup - handle it
            try:
                page.wait_for_selector('[data-testid="search-page-list-container"]', timeout=10000)
            except:
                pass
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            return self._find_property_link(soup)
    
    def _search_with_requests(self, address: str) -> Optional[str]:
        """Fallback search using enhanced requests."""
        search_url = f"https://www.zillow.com/homes/{urllib.parse.quote(address)}/"
        
        headers = self.get_random_headers()
        headers['Referer'] = 'https://www.google.com/'
        
        # Add random delay to simulate human behavior
        time.sleep(random.uniform(1, 3))
        
        response = self.session.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        return self._find_property_link(soup)
    
    def _find_property_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Find the first valid property link from search results."""
        # Try multiple selectors for property links
        selectors = [
            'a[href*="/homedetails/"]',
            'a[data-test="property-card-link"]',
            'a[class*="StyledPropertyCardDataArea"]',
            '.property-card-link'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if '/homedetails/' in href and '_zpid' in href:
                    if href.startswith('/'):
                        return f"https://www.zillow.com{href}"
                    return href
        
        return None
    
    def fetch_property_details(self, query: str) -> Optional[Dict[str, Union[str, int, float]]]:
        """
        Main method to fetch property details.
        Accepts either an address or Zillow URL.
        """
        if not query:
            return None
        
        # Determine if input is URL or address
        if query.startswith('http'):
            property_url = query
        else:
            property_url = self.search_property_url(query)
            if not property_url:
                raise ValueError(f"Could not find property URL for address: {query}")
        
        # Try multiple extraction strategies
        strategies = [
            self._extract_with_scraperapi,
            self._extract_with_playwright,
            self._extract_with_requests
        ]
        
        for strategy in strategies:
            try:
                result = strategy(property_url)
                if result and result.get('address'):
                    return result
            except Exception as e:
                logging.warning(f"Extraction strategy {strategy.__name__} failed: {e}")
                continue
        
        raise RuntimeError("All extraction strategies failed")
    
    def _extract_with_scraperapi(self, url: str) -> Optional[Dict]:
        """Extract property data using ScraperAPI."""
        if not self.scraperapi_key:
            return None
            
        payload = {
            'api_key': self.scraperapi_key,
            'url': url,
            'render': 'true',
            'country_code': 'us',
            'device_type': 'desktop'
        }
        
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=45)
        response.raise_for_status()
        
        return self._parse_property_page(response.text)
    
    def _extract_with_playwright(self, url: str) -> Optional[Dict]:
        """Extract property data using Playwright."""
        if not PLAYWRIGHT_AVAILABLE:
            return None
            
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1366, 'height': 768}
            )
            
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            
            # Navigate with human-like behavior
            # Try multiple wait strategies for better reliability
            try:
                page.goto(url, wait_until='load', timeout=15000)
                page.wait_for_timeout(2000)  # Brief pause for dynamic content
            except Exception:
                # Fallback to domcontentloaded if load fails
                page.goto(url, wait_until='domcontentloaded', timeout=10000)
            page.wait_for_timeout(random.randint(3000, 6000))
            
            # Wait for key content to load
            try:
                page.wait_for_selector('[data-testid="price"]', timeout=10000)
            except:
                pass
            
            content = page.content()
            browser.close()
            
            return self._parse_property_page(content)
    
    def _extract_with_requests(self, url: str) -> Optional[Dict]:
        """Fallback extraction using requests."""
        headers = self.get_random_headers()
        headers['Referer'] = 'https://www.zillow.com/'
        
        time.sleep(random.uniform(2, 4))
        
        response = self.session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        return self._parse_property_page(response.text)
    
    def _parse_property_page(self, html: str) -> Dict[str, Union[str, int, float]]:
        """Parse property details from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize result
        result = {
            'address': None,
            'price': None,
            'beds': None,
            'baths': None,
            'sqft': None,
            'year_built': None,
            'image_url': None,
            'property_type': None,
            'lot_size': None,
            'description': None
        }
        
        # Extract address - try multiple selectors
        address_selectors = [
            '[data-testid="home-details-summary-headline"]',
            'h1[class*="ds-address"]',
            '.ds-home-details-chip h1',
            'h1.notranslate'
        ]
        
        for selector in address_selectors:
            address_elem = soup.select_one(selector)
            if address_elem:
                result['address'] = address_elem.get_text(strip=True)
                break
        
        # Extract price
        price_selectors = [
            '[data-testid="price"]',
            '.ds-estimate-value',
            '.ds-value .ds-text-display-xl',
            '.price-summary .ds-text-display-xl'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract numeric value from price
                price_match = re.search(r'[\$]?([\d,]+)', price_text.replace('$', ''))
                if price_match:
                    result['price'] = price_match.group(1).replace(',', '')
                break
        
        # Extract beds, baths, sqft from facts
        facts_selectors = [
            '.ds-home-fact-list li',
            '.ds-bed-bath-living-area span',
            '[data-testid="bed-bath-item"]'
        ]
        
        for selector in facts_selectors:
            facts = soup.select(selector)
            for fact in facts:
                text = fact.get_text(strip=True).lower()
                
                # Beds
                if 'bd' in text or 'bed' in text:
                    bed_match = re.search(r'(\d+)', text)
                    if bed_match:
                        result['beds'] = int(bed_match.group(1))
                
                # Baths
                elif 'ba' in text or 'bath' in text:
                    bath_match = re.search(r'(\d+\.?\d*)', text)
                    if bath_match:
                        result['baths'] = float(bath_match.group(1))
                
                # Square footage
                elif 'sqft' in text or 'sq ft' in text:
                    sqft_match = re.search(r'([\d,]+)', text)
                    if sqft_match:
                        result['sqft'] = int(sqft_match.group(1).replace(',', ''))
        
        # Extract year built
        year_selectors = [
            '.ds-home-fact-list span:contains("Year built")',
            '.ds-data-col span:contains("Built")'
        ]
        
        for selector in year_selectors:
            year_elem = soup.select_one(selector)
            if year_elem:
                parent = year_elem.find_parent()
                if parent:
                    year_text = parent.get_text()
                    year_match = re.search(r'(\d{4})', year_text)
                    if year_match:
                        result['year_built'] = int(year_match.group(1))
                        break
        
        # Extract main image
        image_selectors = [
            '[data-testid="hero-image"]',
            '.ds-media-col img',
            '.media-stream img'
        ]
        
        for selector in image_selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                result['image_url'] = img.get('src')
                break
        
        # Extract property type
        type_selectors = [
            '.ds-chip span',
            '.property-type',
            '[data-testid="property-type"]'
        ]
        
        for selector in type_selectors:
            type_elem = soup.select_one(selector)
            if type_elem:
                result['property_type'] = type_elem.get_text(strip=True)
                break
        
        # Clean up and validate result
        if not result['address'] and not result['price']:
            raise ValueError("Could not extract basic property information")
        
        return {k: v for k, v in result.items() if v is not None}


class PropertyDataService:
    """
    Service layer for property data collection with multiple fallback strategies.
    Integrates with the property creation workflow.
    """
    
    def __init__(self):
        self.zillow_scraper = ZillowScraperV2()
        
        # Alternative APIs for fallback
        self.rentcast_api_key = os.getenv('RENTCAST_API_KEY')
        self.attom_api_key = os.getenv('ATTOM_API_KEY')
    
    def get_property_data(self, address_or_url: str) -> Dict[str, Union[str, int, float]]:
        """
        Get comprehensive property data with multiple fallback strategies.
        """
        strategies = [
            ('Zillow Scraper', self.zillow_scraper.fetch_property_details),
            ('RentCast API', self._fetch_from_rentcast),
            ('ATTOM API', self._fetch_from_attom),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                logging.info(f"Trying {strategy_name} for property data")
                data = strategy_func(address_or_url)
                
                if data and data.get('address'):
                    logging.info(f"Successfully retrieved data using {strategy_name}")
                    return self._normalize_property_data(data)
                    
            except Exception as e:
                logging.warning(f"{strategy_name} failed: {str(e)}")
                continue
        
        raise RuntimeError("All property data sources failed")
    
    def _fetch_from_rentcast(self, address: str) -> Optional[Dict]:
        """Fetch from RentCast API as fallback."""
        if not self.rentcast_api_key or address.startswith('http'):
            return None
            
        # RentCast API implementation
        # This would require API subscription but provides reliable data
        return None
    
    def _fetch_from_attom(self, address: str) -> Optional[Dict]:
        """Fetch from ATTOM Data API as fallback."""
        if not self.attom_api_key or address.startswith('http'):
            return None
            
        # ATTOM API implementation
        return None
    
    def _normalize_property_data(self, data: Dict) -> Dict:
        """Normalize property data format for consistent usage."""
        return {
            'address': data.get('address', ''),
            'price': self._parse_price(data.get('price')),
            'bedrooms': self._parse_int(data.get('beds')),
            'bathrooms': self._parse_float(data.get('baths')),
            'square_feet': self._parse_int(data.get('sqft')),
            'year_built': self._parse_int(data.get('year_built')),
            'image_url': data.get('image_url', ''),
            'property_type': data.get('property_type', ''),
            'description': data.get('description', '')
        }
    
    def _parse_price(self, price_str: Union[str, int, None]) -> Optional[int]:
        """Parse price string to integer."""
        if not price_str:
            return None
        
        if isinstance(price_str, int):
            return price_str
            
        price_match = re.search(r'[\d,]+', str(price_str).replace('$', ''))
        if price_match:
            return int(price_match.group().replace(',', ''))
        return None
    
    def _parse_int(self, value: Union[str, int, None]) -> Optional[int]:
        """Parse string to integer."""
        if value is None:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value: Union[str, float, None]) -> Optional[float]:
        """Parse string to float."""
        if value is None:
            return None
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return None


# Usage example and testing function
def test_scraper():
    """Test the scraper with a sample property."""
    scraper = ZillowScraperV2()
    
    # Test with the failing URL from the user's issue
    test_url = "https://www.zillow.com/homedetails/824-Carol-St-Fayetteville-NC-28303/53646204_zpid/"
    
    try:
        result = scraper.fetch_property_details(test_url)
        print("Success! Property data extracted:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"Scraper test failed: {e}")
        return None


if __name__ == "__main__":
    # Test the scraper
    test_scraper()