import pandas as pd
import requests
import json
import os
import time
import random

# Flink API Configuration
API_BASE_URL = 'https://srv.getflink.pro/api/v1' 
PRODUCT_ENDPOINT = f"{API_BASE_URL}/product/new"
HUB_ENDPOINT = f"{API_BASE_URL}/feed" # Endpoint for articles/posts in The Hub

def load_tokens():
    token_path = 'data/tokens.txt'
    if not os.path.exists(token_path):
        print(f"Warning: {token_path} not found. Creating a placeholder.")
        with open(token_path, 'w') as f:
            f.write("# Add your Flink Auth Tokens here (one per line)\n")
        return []
    
    with open(token_path, 'r') as f:
        tokens = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return tokens

def sync_posts_to_flink():
    csv_path = 'data/Post.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Ensure the file exists in data/ folder.")
        return

    tokens = load_tokens()
    if not tokens:
        print("Error: No tokens found in data/tokens.txt. Please add at least one account token.")
        return

    print(f"--- Flink Hub Uploader (Account Rotation Enabled) ---")
    print(f"Loaded {len(tokens)} accounts for rotation.")

    # Read the posts data
    df = pd.read_csv(csv_path)
    
    success_count = 0
    fail_count = 0

    print(f"--- Uploading {len(df)} posts to Flink Hub... ---")

    for index, row in df.iterrows():
        # Rotate tokens: pick a different account for each post to avoid "hurting the algorithm"
        current_token = tokens[index % len(tokens)]
        
        headers = {
            'Authorization': f'Bearer {current_token}',
            'Content-Type': 'application/json'
        }

        try:
            topic = str(row.get('Topics', 'General'))
            details = str(row.get('Details', ''))
            post_type = str(row.get('Type', 'Insight'))

            # Construct payload for The Hub
            payload = {
                "title": f"{topic} {post_type}",
                "body": details,
                "category": topic,
                "type": post_type.lower(),
                "status": "published"
            }

            print(f"[{index+1}/{len(df)}] Uploading as Account {index % len(tokens) + 1}...")
            response = requests.post(HUB_ENDPOINT, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                print(f"  SUCCESS: {topic} - {post_type}")
                success_count += 1
            else:
                print(f"  FAILED: {topic} - Status: {response.status_code} - {response.text[:100]}")
                fail_count += 1
            
            # Add a small random delay to look more human
            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"  ERROR on index {index+1}: {e}")
            fail_count += 1

    print(f"\n--- Post Sync Complete ---")
    print(f"Uploaded: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    # You can choose which one to run or implement a simple CLI
    sync_posts_to_flink()

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
