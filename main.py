import os
import pandas as pd
from src.crapy import crapy

def main():
    # 1. Ensure folders exist
    for folder in ['data', 'rules']:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # 2. Configuration
    target_url = 'https://jiji.ng/agriculture-and-foodstuff'

    print(f"--- Starting Phone-Hunter Scraper: {target_url} ---")

    # 3. Initialize scraper
    scraper_tool = crapy()
    
    # 4. Get data (Limited to 15 for demonstration as phone scraping is slower)
    results = scraper_tool.get_data(target_url, max_items=300)

    if results:
        # 5. Create DataFrame
        df = pd.DataFrame(results)
        
        # Keep the fields we can reliably sync into Flink.
        cols_to_save = [
            'product_name',
            'price',
            'location',
            'category',
            'description',
            'seller_name',
            'seller_phone',
            'link',
        ]
        
        # If some fields didn't populate, avoid KeyError
        existing_cols = [c for c in cols_to_save if c in df.columns]
        output_df = df[existing_cols]
        
        output_path = 'data/crapy_results.csv'
        output_df.to_csv(output_path, index=False)
        
        print(f"\n--- Success! Data saved. ---")
        print(output_df.head())
        print(f"\n--- File location: {output_path} ---")
    else:
        print("--- No data found. ---")

if __name__ == "__main__":
    main()
