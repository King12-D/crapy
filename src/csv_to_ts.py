import csv
import json
import re
import os

CSV_PATH = "data/crapy_results.csv"
OUT_PATH = "../Flink/server/src/scripts/simulate/seed-data/scraped-products.ts"

def parse_price(price_str: str) -> int:
    cleaned = re.sub(r"[^\d]", "", price_str)
    return int(cleaned) if cleaned else 0

def parse_images(images_str: str) -> list[str]:
    try:
        return json.loads(images_str.replace("'", '"'))
    except:
        return []

def convert():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found. Run the scraper first.")
        return

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
                "mainImage": main_image,
                "images": all_images,
                "seller": seller or "Unknown",
            })

    lines = [
        'export interface ScrapedProduct {',
        '  name: string;',
        '  price: number;',
        '  images: string[];',
        '  mainImage: string;',
        '  seller: string;',
        '}',
        '',
        'export const SCRAPED_PRODUCTS: ScrapedProduct[] = [',
    ]

    for p in products:
        images_json = json.dumps(p["images"], indent=6)
        images_json = "      " + images_json.replace("\n", "\n      ")
        lines.append("  {")
        lines.append(f'    name: {json.dumps(p["name"])},')
        lines.append(f'    price: {p["price"]},')
        lines.append(f'    mainImage: {json.dumps(p["mainImage"])},')
        lines.append(f"    images: {images_json},")
        lines.append(f'    seller: {json.dumps(p["seller"])},')
        lines.append("  },")

    lines.append("];")
    lines.append("")

    out = "\n".join(lines)

    with open(OUT_PATH, "w") as f:
        f.write(out)

    print(f"Exported {len(products)} products to {OUT_PATH}")

if __name__ == "__main__":
    convert()
