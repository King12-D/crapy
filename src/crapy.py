from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse
import random

class crapy:
    def __init__(self):
        # Precise Nigerian phone regex for scraping
        self.phone_pattern = re.compile(r'(?:\+234|0)[789][01][\s-]?\d{3}[\s-]?\d{4,5}')

    def _category_from_link(self, link: str) -> str:
        try:
            path = urlparse(link).path.strip("/")
            parts = [p for p in path.split("/") if p]
            return parts[1].strip().lower() if len(parts) >= 2 else "agriculture-and-foodstuff"
        except:
            return "agriculture-and-foodstuff"
        
    def get_data(self, url, max_items=50):
        """
        Simplified scraper: No scrolling to minimize bot detection triggers.
        """
        options = webdriver.FirefoxOptions()
        # Ensure it's not headless so the user can potentially see/solve challenges
        
        # User-Agent spoofing
        options.set_preference("general.useragent.override", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0")
        
        driver = None
        try:
            print(f"--- Navigating to: {url} ---")
            try:
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
            except:
                driver = webdriver.Firefox(options=options)

            driver.get(url)
            
            # Wait for content to potentially load
            print(f"--- Waiting for page load... (Current Title: {driver.title}) ---")
            time.sleep(10) 
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Attempt to find items with multiple selectors
            containers = soup.select('.js-advert-list-item')
            if not containers:
                containers = soup.select('div[data-advert-id]')
            if not containers:
                containers = [a.parent for a in soup.select('a.qa-advert-list-item') if a.parent]

            print(f"--- Found {len(containers)} items on the page ---")
            
            initial_data = []
            for item in containers:
                try:
                    title_el = item.select_one('.qa-advert-title, .b-advert-title-inner')
                    price_el = item.select_one('.qa-advert-price, .b-list-advert__price')
                    link_el = item.find('a', href=True)
                    
                    if title_el and price_el and link_el:
                        link = "https://jiji.ng" + link_el['href'] if link_el['href'].startswith('/') else link_el['href']
                        initial_data.append({
                            'product_name': title_el.get_text(strip=True),
                            'price': price_el.get_text(strip=True),
                            'location': 'N/A',
                            'link': link,
                            'category': self._category_from_link(link),
                        })
                except: continue
            
            results = []
            # Only visit details if we found listing links
            for i, entry in enumerate(initial_data[:max_items]):
                print(f"--- Item {i+1}/{len(initial_data)}: {entry['product_name'][:30]} ---")
                try:
                    driver.get(entry['link'])
                    time.sleep(random.uniform(3, 6))
                    
                    item_soup = BeautifulSoup(driver.page_source, 'lxml')
                    seller_el = item_soup.select_one('.b-seller-block__name')
                    entry['seller_name'] = seller_el.get_text(strip=True) if seller_el else 'Private Seller'
                    
                    desc_el = item_soup.select_one('.qa-description-text')
                    desc_text = desc_el.get_text(strip=True) if desc_el else ''
                    matches = self.phone_pattern.findall(desc_text)
                    entry['seller_phone'] = matches[0] if matches else "Visit Link"
                    entry['seller_email'] = "N/A"
                    
                    results.append(entry)
                except:
                    results.append(entry)
            
            return results
        finally:
            if driver:
                driver.quit()
