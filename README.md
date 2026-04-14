# Crapy - Flink Agriculture Scraper

A robust web scraper designed for **Flink** to extract agriculture and food product data from Jiji.ng.

## Features
- **Headless Firefox**: Runs in the background using Selenium and Geckodriver.
- **Agriculture Focus**: Specifically configured to scrape the `Agriculture & Foodstuff` category.
- **Data Export**: Saves results to `data/crapy_results.csv`.
- **Structured Data**: Extracts Product Name, Price, Location, and Seller Name.

## Prerequisites
- Python 3.12+
- Firefox Browser
- Active Virtual Environment

## Installation
1. Clone the repository.
2. Create and activate a venv:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the main script:
```bash
python main.py
```

## Data Output
The scraper generates a CSV file in the `data/` folder with the following columns:
- `product_name`
- `price`
- `location`
- `seller_name`
- `product_url`
