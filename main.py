import os
import sys
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from src.crapy import crapy
from src.sync_to_mongo import sync

def scrape():
    for folder in ['data', 'rules']:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # 2. Configuration for Flink (Agriculture Products)
    target_url = 'https://jiji.ng/agriculture-and-foodstuff'
    print(f"--- Starting scraper ---")

    # 3. Initialize our scraper
    scraper_tool = crapy()
    results = scraper_tool.get_data(target_url, max_items=500)

    if results:
        # 5. Save the data to a CSV in the data/ folder
        df = pd.DataFrame(results)
        output_path = 'data/crapy_results.csv'
        df.to_csv(output_path, index=False)
        print(f"\n--- SUCCESS! Found {len(results)} items. ---")
        return True
    else:
        print("\n--- FAILED: No items found. ---")
        return False

def main():
    args = set(sys.argv[1:])

    if "--sync-only" in args:
        print("--- Syncing existing scraped data to MongoDB ---")
        sync()
        return

    scraped = scrape()

    if scraped and ("--sync" in args or "--sync-only" in args):
        print("\n--- Syncing to MongoDB ---")
        sync()

if __name__ == "__main__":
    main()
