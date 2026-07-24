import csv
import json
import re
import os
from datetime import datetime, timezone
from pymongo import MongoClient

CSV_PATH = "data/crapy_results.csv"
MONGO_URI = os.getenv("DBURI")
DB_NAME = "flink"
COLLECTION_NAME = "_scraped_products"

def parse_price(price_str: str) -> float:
    cleaned = re.sub(r"[^\d.]", "", price_str.replace(",", ""))
    return float(cleaned) if cleaned else 0.0

def parse_images(images_str: str) -> list[str]:
    try:
        return json.loads(images_str.replace("'", '"'))
    except:
        return []

def infer_category(name: str) -> str:
    lower = name.lower()
    if any(k in lower for k in ["fish feed", "catfish", "aqua"]): return "fish-feed"
    if any(k in lower for k in ["feed", "premix", "breeder", "lick"]): return "animal-feed"
    if any(k in lower for k in ["supplement", "mineral", "herbal"]): return "supplements"
    if any(k in lower for k in ["fertilizer", "insecticide", "agrovert"]): return "inputs"
    if any(k in lower for k in ["seed", "sammaz", "maize"]): return "seeds"
    if any(k in lower for k in ["grain", "barley", "corn", "plantain"]): return "grains"
    return "crops"

def sync():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found")
        return

    print(f"Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        products = []

        for row in reader:
            name = row.get("product_name", "").strip()
            price = parse_price(row.get("price", "0"))
            main_image = row.get("main_image", "").strip()
            all_images = parse_images(row.get("all_images", "[]"))
            seller = row.get("seller_name", "").strip()

            if not name or not main_image:
                continue

            products.append({
                "name": name,
                "price": price,
                "category": infer_category(name),
                "images": [main_image] + [img for img in all_images if img != main_image],
                "unit": "piece",
                "quantityAvailable": 100,
                "description": f"Quality {name} available for sale.",
                "isActive": True,
                "scrapedFrom": "jiji",
                "scrapedAt": datetime.now(timezone.utc),
                "sellerName": seller or "Unknown",
            })

    if products:
        collection.delete_many({})  # replace old scraped data
        collection.insert_many(products)
        print(f"Uploaded {len(products)} scraped products to MongoDB.{COLLECTION_NAME}")
    else:
        print("No products to upload")

    client.close()

if __name__ == "__main__":
    sync()
