from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re
import random
import os

class crapy:
    def __init__(self):
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
        # options.add_argument('--headless')
        
        # --- ENHANCED STEALTH FOR CLOUDFLARE ---
        ua = "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0"
        options.set_preference("general.useragent.override", ua)
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference('useAutomationExtension', False)
        options.set_preference("intl.accept_languages", "en-US, en")
        
        # Set a common window size
        options.add_argument("--width=1366")
        options.add_argument("--height=768")

        # Driver path logic
        gecko_path = "/home/king-dav/.wdm/drivers/geckodriver/linux64/v0.36.0/geckodriver"
        if not os.path.exists(gecko_path):
             try: gecko_path = GeckoDriverManager().install()
             except: raise Exception("Geckodriver not found. Rate limit active.")

        driver = webdriver.Firefox(service=FirefoxService(gecko_path), options=options)

        try:
            print(f"--- Navigating to: {url} ---")
            driver.get(url)
            
            # Wait for Cloudflare to do its thing (can take 10-20 seconds)
            print("--- Waiting for Cloudflare (25s)... ---")
            time.sleep(25)
            
            # Check Title
            if "Just a moment" in driver.title:
                print(f"--- Still blocked by Cloudflare. Title: {driver.title} ---")
                # Try a small scroll to see if it triggers resolution
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(5)
            
            # Scroll multiple times like a user
            for i in range(4):
                amount = random.randint(300, 800)
                driver.execute_script(f"window.scrollBy(0, {amount});")
                time.sleep(random.uniform(2, 4))
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Selectors
            selectors = ['.js-advert-list-item', '.b-advert-listing-item', 'div[class*="advert-list-item"]']
            containers = []
            for sel in selectors:
                containers = soup.select(sel)
                if containers:
                    print(f"--- Success! Found {len(containers)} items ---")
                    break
            
            if not containers:
                print(f"--- No items found. Is there a captcha? Title: {driver.title} ---")
                return []
            
            # Processing...
            results = []
            for i, entry in enumerate(containers[:max_items]):
                try:
                    title_el = entry.select_one('.qa-advert-title')
                    price_el = entry.select_one('.qa-advert-price')
                    link_el = entry.find('a', href=True)
                    img_el = entry.select_one('img')
                    
                    if title_el and price_el and link_el:
                        prod = {
                            'product_name': title_el.get_text(strip=True),
                            'price': price_el.get_text(strip=True),
                            'location': 'N/A', # Simple version for listing
                            'link': "https://jiji.ng" + link_el['href'],
                            'main_image': img_el.get('src') or img_el.get('data-src') if img_el else 'None'
                        }
                        results.append(prod)
                except: continue
            
            # For each result, get details (optional but requested)
            final_results = []
            for i, prod in enumerate(results):
                print(f"--- Scraping details {i+1}/{len(results)}: {prod['product_name'][:20]} ---")
                driver.get(prod['link'])
                time.sleep(random.uniform(5, 8))
                
                it_soup = BeautifulSoup(driver.page_source, 'lxml')
                
                # Seller & Phone
                seller_el = it_soup.select_one('.b-seller-block__name')
                prod['seller_name'] = seller_el.get_text(strip=True) if seller_el else 'Private'
                
                # Phone search in text
                desc_el = it_soup.select_one('.qa-description-text')
                desc_text = desc_el.get_text(strip=True) if desc_el else ''
                matches = self.phone_pattern.findall(desc_text)
                prod['seller_phone'] = matches[0] if matches else "Contact on Jiji"
                
                # Images
                g_imgs = it_soup.select('.b-advert-carousel img')
                prod['all_images'] = list(set([img.get('src') or img.get('data-src') for img in g_imgs if img.get('src') or img.get('data-src')]))
                
                final_results.append(prod)
                print(f"    Done: {prod['seller_name']}")
                
            return final_results
        finally:
            if driver:
                driver.quit()
