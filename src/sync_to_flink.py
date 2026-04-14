import requests
import json
import os
import csv
from urllib.parse import urlparse

# Flink API Configuration
# Default points to your deployed server routes (/api/v1/*).
# Override with env var if needed, e.g.:
#   export FLINK_API_BASE_URL="http://localhost:3000/api/v1"
API_BASE_URL = os.getenv("FLINK_API_BASE_URL", "https://srv.getflink.pro/api/v1")
SYNC_ENDPOINT = f"{API_BASE_URL}/product/new"

def clean_price(price_str):
    try:
        # Remove currency symbol and commas: ₦ 30,000 -> 30000
        clean = price_str.replace('₦', '').replace(',', '').strip()
        return float(clean)
    except:
        return 0.0

def parse_location(loc_str):
    # Jiji format: "Lagos, Ojo"
    parts = loc_str.split(',')
    state = parts[0].strip() if len(parts) > 0 else "Unknown"
    city = parts[1].strip() if len(parts) > 1 else state
    return {
        "state": state,
        "city": city,
        "address": loc_str
    }

def category_from_link(link: str) -> str:
    try:
        path = urlparse(str(link)).path.strip("/")
        parts = [p for p in path.split("/") if p]
        return parts[1].strip().lower() if len(parts) >= 2 else "agriculture-and-foodstuff"
    except:
        return "agriculture-and-foodstuff"

def normalize_category(value: str) -> str:
    value = str(value or "").strip().lower()
    return value or "agriculture-and-foodstuff"

def iter_rows(csv_path: str):
    """
    Iterate rows as dicts. Uses pandas if available, else falls back to csv module.
    """
    try:
        import pandas as pd  # type: ignore

        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            yield {k: row.get(k) for k in df.columns}
        return
    except Exception:
        # pandas missing or failed: use csv
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

def sync_to_flink():
    csv_path = 'data/crapy_results.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run the scraper first.")
        return

    print("--- Flink Product Uploader ---")
    token = input("Enter your Flink Auth Token (Bearer): ").strip()
    
    if not token:
        print("Error: Auth token is required.")
        return

    # Accept both raw JWT and already prefixed "Bearer <token>"
    token = token.replace("Bearer ", "").strip()
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    success_count = 0
    fail_count = 0

    rows = list(iter_rows(csv_path))
    print(f"--- Uploading {len(rows)} products to Flink... ---")

    for index, row in enumerate(rows):
        row = row or {}
        # Prepare the payload based on Flink API requirements
        link = str(row.get("link") or "").strip()
        scraped_desc = str(row.get("description") or "").strip()
        seller_name = str(row.get("seller_name") or "Private Seller").strip()
        seller_phone = str(row.get("seller_phone") or "").strip()
        category = normalize_category(row.get("category")) if row.get("category") else normalize_category(category_from_link(link))

        meta_bits = [f"Seller: {seller_name}"]
        if seller_phone and seller_phone.lower() not in ["visit link to view", "not found in description", "nan"]:
            meta_bits.append(f"Phone: {seller_phone}")
        if link:
            meta_bits.append(f"Source: {link}")

        payload = {
            "name": str(row.get('product_name') or '').strip(),
            "category": category,
            "description": (scraped_desc + "\n\n" + ". ".join(meta_bits)).strip() if scraped_desc else ". ".join(meta_bits),
            "price": clean_price(str(row.get('price') or '')),
            "unit": "piece",
            "quantityAvailable": 10,
            "location": parse_location(str(row.get('location') or '')),
            "images": [] # Jiji images would need to be downloaded/uploaded separately
        }

        try:
            if not payload["name"]:
                print(f"SKIP [{index+1}]: Missing product_name")
                continue
            response = requests.post(SYNC_ENDPOINT, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 201 or response.status_code == 200:
                print(f"SUCCESS [{index+1}]: {payload['name']}")
                success_count += 1
            else:
                print(f"FAILED [{index+1}]: {payload['name']} - Status: {response.status_code}")
                # print(response.text)
                fail_count += 1
        except Exception as e:
            print(f"ERROR: {e}")
            fail_count += 1

    print(f"\n--- Sync Complete ---")
    print(f"Uploaded: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    sync_to_flink()
