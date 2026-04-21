import pandas as pd
import requests
import json
import os
import ast

# Flink API Configuration
API_BASE_URL = 'https://srv.getflink.pro/api/v1' 
SYNC_ENDPOINT = f"{API_BASE_URL}/product/new"

def clean_price(price_str):
    try:
        clean = str(price_str).replace('₦', '').replace(',', '').strip()
        return float(clean)
    except:
        return 0.0

def parse_location(loc_str):
    parts = str(loc_str).split(',')
    state = parts[0].strip() if len(parts) > 0 else "Unknown"
    city = parts[1].strip() if len(parts) > 1 else state
    return {
        "state": state,
        "city": city,
        "address": loc_str
    }

def parse_images(img_val):
    if pd.isna(img_val):
        return []
    try:
        #all_images in CSV is saved as a string "[url1, url2]"
        return ast.literal_eval(str(img_val))
    except:
        return [str(img_val)] if str(img_val).startswith('http') else []

def sync_to_flink():
    csv_path = 'data/crapy_results.csv'
    if not os.path.exists(csv_path):
        print(f"Error: Run the scraper first.")
        return

    print("--- Flink Product Uploader (with Images) ---")
    token = input("Enter your Flink Auth Token: ").strip()
    if not token: return

    df = pd.read_csv(csv_path)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    success_count = 0
    for index, row in df.iterrows():
        # Prepare the payload
        payload = {
            "name": row['product_name'],
            "category": "Agriculture",
            "description": f"Seller: {row['seller_name']}. Phone: {row['seller_phone']}",
            "price": clean_price(row['price']),
            "unit": "unit",
            "quantityAvailable": 10,
            "location": parse_location(row['location']),
            "images": parse_images(row.get('all_images', row.get('main_image', [])))
        }

        try:
            response = requests.post(SYNC_ENDPOINT, headers=headers, json=payload)
            if response.status_code in [200, 201]:
                print(f"SUCCESS: {row['product_name']}")
                success_count += 1
            else:
                print(f"FAILED: {row['product_name']} ({response.status_code})")
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\n--- Sync Complete. Uploaded {success_count} products. ---")

if __name__ == "__main__":
    sync_to_flink()
