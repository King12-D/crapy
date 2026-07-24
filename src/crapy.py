import cloudscraper
from bs4 import BeautifulSoup
import time
import re
import random

class crapy:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.phone_pattern = re.compile(r'(?:\+234|0)[789][01][\s-]?\d{3}[\s-]?\d{4,5}')

    def get_data(self, url, max_items=50):
        print(f"--- Fetching listing page: {url} ---")
        resp = self.scraper.get(url, timeout=30)
        if resp.status_code != 200:
            print(f"--- HTTP {resp.status_code} ---")
            return []

        soup = BeautifulSoup(resp.text, 'lxml')

        selectors = ['.qa-advert-list-item', '.b-advert-listing-item', 'div[class*="advert-list-item"]', '.js-advert-list-item']
        containers = []
        for sel in selectors:
            containers = soup.select(sel)
            if containers:
                print(f"--- Found {len(containers)} items ---")
                break

        if not containers:
            print("--- No items found ---")
            return []

        results = []
        for i, entry in enumerate(containers[:max_items]):
            try:
                title_el = entry.select_one('.qa-advert-title')
                price_el = entry.select_one('.qa-advert-price')
                img_el = entry.select_one('img')

                if title_el and price_el:
                    href = entry.get('href')
                    if not href:
                        continue
                    link = href if href.startswith('http') else f"https://jiji.ng{href}"
                    prod = {
                        'product_name': title_el.get_text(strip=True),
                        'price': price_el.get_text(strip=True),
                        'location': 'N/A',
                        'link': link,
                        'main_image': img_el.get('src') or img_el.get('data-src') if img_el else 'None'
                    }
                    results.append(prod)
            except:
                continue

        final_results = []
        for i, prod in enumerate(results):
            print(f"--- Scraping details {i+1}/{len(results)}: {prod['product_name'][:20]} ---")
            try:
                d_resp = self.scraper.get(prod['link'], timeout=30)
                it_soup = BeautifulSoup(d_resp.text, 'lxml')

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
            except Exception as e:
                print(f"    Failed: {e}")
                continue

            time.sleep(random.uniform(2, 4))

        return final_results
