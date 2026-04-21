from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re

class crapy:
    def __init__(self):
        # Precise Nigerian phone regex for scraping
        self.phone_pattern = re.compile(r'(?:\+234|0)[789][01][\s-]?\d{3}[\s-]?\d{4,5}')
        
    def get_data(self, url, max_items=15):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

        try:
            print(f"--- Navigating to Listing: {url} ---")
            driver.get(url)
            time.sleep(5)
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            containers = soup.select('.js-advert-list-item')
            print(f"--- Found {len(containers)} items ---")
            
            initial_data = []
            for item in containers:
                try:
                    title_el = item.select_one('.qa-advert-title')
                    price_el = item.select_one('.qa-advert-price')
                    location_el = item.select_one('.b-list-advert__region__text')
                    link_el = item.find('a', href=True)
                    
                    # EXTRACT IMAGE from listing card
                    img_el = item.select_one('img')
                    img_url = img_el.get('src') or img_el.get('data-src') if img_el else 'None'
                    
                    if title_el and price_el and link_el:
                        initial_data.append({
                            'product_name': title_el.get_text(strip=True),
                            'price': price_el.get_text(strip=True),
                            'location': location_el.get_text(strip=True) if location_el else 'N/A',
                            'link': "https://jiji.ng" + link_el['href'] if link_el['href'].startswith('/') else link_el['href'],
                            'main_image': img_url
                        })
                except: continue
            
            results = []
            for i, entry in enumerate(initial_data[:max_items]):
                print(f"--- Item {i+1}/{max_items}: {entry['product_name'][:25]} ---")
                try:
                    driver.get(entry['link'])
                    time.sleep(3)
                    
                    item_soup = BeautifulSoup(driver.page_source, 'lxml')
                    
                    # 1. Seller Name
                    seller_el = item_soup.select_one('.b-seller-block__name')
                    entry['seller_name'] = seller_el.get_text(strip=True) if seller_el else 'Private Seller'
                    
                    # 2. Additional Images (Gallery)
                    gallery_imgs = item_soup.select('.b-advert-carousel img')
                    entry['all_images'] = list(set([img.get('src') or img.get('data-src') for img in gallery_imgs if img.get('src') or img.get('data-src')]))
                    
                    # 3. Extract Phone
                    desc_el = item_soup.select_one('.qa-description-text')
                    desc_text = desc_el.get_text(strip=True) if desc_el else ''
                    matches = self.phone_pattern.findall(desc_text)
                    
                    if matches:
                        entry['seller_phone'] = matches[0]
                    else:
                        try:
                            # Try Reveal
                            btn = driver.find_element(By.CSS_SELECTOR, '.qa-show-contact')
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(2)
                            new_matches = self.phone_pattern.findall(driver.page_source)
                            entry['seller_phone'] = new_matches[0] if new_matches else "Visit Link"
                        except:
                            entry['seller_phone'] = "Not Found"
                    
                    print(f"    Seller: {entry['seller_name']} | Images: {len(entry['all_images'])}")
                    results.append(entry)
                except:
                    results.append(entry)
            
            return results
        finally:
            driver.quit()
