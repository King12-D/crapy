import csv
import json
import re
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "crapy_results.csv")
DB_NAME = "flink"
COLLECTION_NAME = "_scraped_products"
MAX_PRODUCTS = 5000

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
    load_dotenv()
    mongo_uri = os.getenv("DBURI")
    if not mongo_uri:
        print("Error: DBURI not set in .env or environment")
        return

    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found")
        return

    print(f"Connecting to MongoDB...")
    client = MongoClient(mongo_uri)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        operations = []

        for row in reader:
            name = row.get("product_name", "").strip()
            price = parse_price(row.get("price", "0"))
            link = row.get("link", "").strip()
            main_image = row.get("main_image", "").strip()
            all_images = parse_images(row.get("all_images", "[]"))
            seller = row.get("seller_name", "").strip()

            if not name or not main_image or not link:
                continue

            operations.append(UpdateOne(
                {"link": link},
                {"$set": {
                    "name": name,
                    "price": price,
                    "link": link,
                    "category": infer_category(name),
                    "images": [main_image] + [img for img in all_images if img != main_image],
                    "unit": "piece",
                    "quantityAvailable": 100,
                    "description": f"Quality {name} available for sale.",
                    "isActive": True,
                    "scrapedFrom": "jiji",
                    "scrapedAt": datetime.now(timezone.utc),
                    "sellerName": seller or "Unknown",
                }},
                upsert=True,
            ))

    if operations:
        result = collection.bulk_write(operations)
        total = collection.count_documents({})
        print(f"Upserted {len(operations)} products (inserted: {result.upserted_count}, modified: {result.modified_count}, total in DB: {total})")

        if total > MAX_PRODUCTS:
            excess = total - MAX_PRODUCTS
            old = collection.find().sort("scrapedAt", 1).limit(excess)
            old_ids = [doc["_id"] for doc in old]
            collection.delete_many({"_id": {"$in": old_ids}})
            print(f"Trimmed {len(old_ids)} oldest, keeping at {MAX_PRODUCTS}")
    else:
        print("No products to upload")

    client.close()

if __name__ == "__main__":
    sync()
