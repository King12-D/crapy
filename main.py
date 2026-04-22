import os
import pandas as pd
from src.crapy import crapy

def main():
    # 1. Ensure our output folders exist
    for folder in ['data', 'rules']:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # 2. Configuration for Flink (Agriculture Products)
    target_url = 'https://jiji.ng/agriculture-and-foodstuff'

    print(f"--- Starting Advanced Scraper for Flink: {target_url} ---")
    print("--- Note: Scraping emails and phone numbers depends on seller privacy settings ---")

    # 3. Initialize our scraper
    scraper_tool = crapy()
    
    # 4. Run the scraping logic (targeting ~50 items to show multi-page support)
    results = scraper_tool.get_data(target_url, max_items=50)

    if results:
        # 5. Save the data to a CSV in the data/ folder
        df = pd.DataFrame(results)
        
        # Reorder columns for better readability
        cols = ['product_name', 'price', 'location', 'seller_name', 'seller_email', 'seller_phone', 'link']
        df = df[cols]
        
        output_path = 'data/crapy_results.csv'
        df.to_csv(output_path, index=False)
        
        print(f"\n--- Success! Found {len(results)} items. ---")
        print(df[['product_name', 'seller_name', 'seller_email']].head(10)) # Show a preview
        print(f"\n--- Data saved to: {output_path} ---")
    else:
        print("--- No data found. ---")

if __name__ == "__main__":
    main()
