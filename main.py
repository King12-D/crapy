import os
import pandas as pd
from src.crapy import crapy

def main():
    # 1. Folders
    for folder in ['data', 'rules']:
        if not os.path.exists(folder):
            os.makedirs(folder)

    target_url = 'https://jiji.ng/agriculture-and-foodstuff'
    print(f"--- Starting Image-Enriched Scraper for Flink ---")

    scraper_tool = crapy()
    results = scraper_tool.get_data(target_url, max_items=15)

    if results:
        df = pd.DataFrame(results)
        
        # Columns: Name, Price, Location, Seller, Phone, Images
        cols_to_save = ['product_name', 'price', 'location', 'seller_name', 'seller_phone', 'main_image', 'all_images']
        output_df = df[[c for c in cols_to_save if c in df.columns]]
        
        output_path = 'data/crapy_results.csv'
        output_df.to_csv(output_path, index=False)
        
        print(f"\n--- Success! Found {len(results)} items with images. ---")
        print(output_df[['product_name', 'seller_phone', 'main_image']].head())
    else:
        print("--- No data found. ---")

if __name__ == "__main__":
    main()
