from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

class crapy:
    def __init__(self):
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        
    def get_data(self, url, max_items=50):
        # Setup headless Firefox
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

        try:
            print(f"--- Navigating to Listing: {url} ---")
            driver.get(url)
            time.sleep(5)
            
            # Scroll multiple times to get more items
            # Each scroll usually loads ~24 more items
            for i in range(5):
                print(f"--- Scrolling ({i+1}/5) ---")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            containers = soup.select('.js-advert-list-item')
            print(f"--- Found {len(containers)} containers on listing page ---")
            
            initial_data = []
            for item in containers:
                try:
                    title_el = item.select_one('.qa-advert-title')
                    price_el = item.select_one('.qa-advert-price')
                    location_el = item.select_one('.b-list-advert__region__text')
                    link_el = item.find('a', href=True)
                    
                    if title_el and price_el and link_el:
                        initial_data.append({
                            'product_name': title_el.get_text(strip=True),
                            'price': price_el.get_text(strip=True),
                            'location': location_el.get_text(strip=True) if location_el else 'N/A',
                            'link': "https://jiji.ng" + link_el['href'] if link_el['href'].startswith('/') else link_el['href']
                        })
                except:
                    continue
            
            # Limit total items for safety
            data_to_process = initial_data[:max_items]
            results = []
            
            print(f"--- Processing top {len(data_to_process)} items for seller details ---")
            
            for i, entry in enumerate(data_to_process):
                print(f"--- Visiting Item {i+1}/{len(data_to_process)}: {entry['product_name'][:30]}... ---")
                try:
                    driver.get(entry['link'])
                    time.sleep(3) # Wait for load
                    
                    item_soup = BeautifulSoup(driver.page_source, 'lxml')
                    
                    # 1. Seller Name
                    seller_el = item_soup.select_one('.b-seller-block__name')
                    entry['seller_name'] = seller_el.get_text(strip=True) if seller_el else 'Unknown'
                    
                    # 2. Description & Email
                    desc_el = item_soup.select_one('.qa-description-text')
                    desc_text = desc_el.get_text(strip=True) if desc_el else ''
                    emails = self.email_pattern.findall(desc_text)
                    entry['seller_email'] = ", ".join(emails) if emails else 'Not listed in description'
                    
                    # 3. Phone (Optional/Experimental - requires click)
                    # We only do this for the first few to avoid heavy rate limiting
                    if i < 10: # Only try for top 10
                         try:
                             # Wait for button and click
                             btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.qa-show-contact')))
                             btn.click()
                             time.sleep(2)
                             phone_el = driver.find_element(By.CSS_SELECTOR, '.b-button__text') # Button text usually changes to phone
                             entry['seller_phone'] = phone_el.text.strip()
                         except:
                             entry['seller_phone'] = 'Click to view'
                    else:
                        entry['seller_phone'] = 'Available on web'
                        
                    results.append(entry)
                except Exception as e:
                    print(f"Error on {entry['link']}: {e}")
                    results.append(entry)
            
            return results
        
        finally:
            driver.quit()
