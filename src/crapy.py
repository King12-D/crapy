import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import re
import random

class crapy:
    def __init__(self):
        self.phone_pattern = re.compile(r'(?:\+234|0)[789][01][\s-]?\d{3}[\s-]?\d{4,5}')

    def get_data(self, url, max_items=50):
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--lang=en-US")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

        driver = uc.Chrome(options=options, version_main=150)

        try:
            print(f"--- Navigating to: {url} ---")
            driver.get(url)

            print("--- Waiting for page load (10s)... ---")
            time.sleep(10)

            if "Just a moment" in driver.title:
                print(f"--- Still blocked by Cloudflare. Title: {driver.title} ---")
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(5)

            for i in range(4):
                amount = random.randint(300, 800)
                driver.execute_script(f"window.scrollBy(0, {amount});")
                time.sleep(random.uniform(2, 4))

            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

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
                            'location': 'N/A',
                            'link': "https://jiji.ng" + link_el['href'],
                            'main_image': img_el.get('src') or img_el.get('data-src') if img_el else 'None'
                        }
                        results.append(prod)
                except: continue

            final_results = []
            for i, prod in enumerate(results):
                print(f"--- Scraping details {i+1}/{len(results)}: {prod['product_name'][:20]} ---")
                driver.get(prod['link'])
                time.sleep(random.uniform(5, 8))

                it_soup = BeautifulSoup(driver.page_source, 'lxml')

                seller_el = it_soup.select_one('.b-seller-block__name')
                prod['seller_name'] = seller_el.get_text(strip=True) if seller_el else 'Private'

                desc_el = it_soup.select_one('.qa-description-text')
                desc_text = desc_el.get_text(strip=True) if desc_el else ''
                matches = self.phone_pattern.findall(desc_text)
                prod['seller_phone'] = matches[0] if matches else "Contact on Jiji"

                g_imgs = it_soup.select('.b-advert-carousel img')
                prod['all_images'] = list(set([img.get('src') or img.get('data-src') for img in g_imgs if img.get('src') or img.get('data-src')]))

                final_results.append(prod)
                print(f"    Done: {prod['seller_name']}")

            return final_results
        finally:
            driver.quit()
