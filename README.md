# Crapy - Flink Agriculture Scraper

A robust web scraper designed for **Flink** to extract agriculture products and seller contacts from Jiji.ng and sync them to the Flink mobile app.

## Features
- **Phone Extraction**: Automatically clicks protected "Show contact" buttons to reveal seller phone numbers.
- **Agriculture Focus**: Optimized for the `Agriculture & Foodstuff` category.
- **Clean Data**: Exports only relevant fields to CSV (no URLs).
- **Flink Sync**: Includes an uploader script to push data to the Flink API.

## Prerequisites
- Python 3.12+
- Firefox Browser
- Active Virtual Environment

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Scrape Data
Run the main script to fetch products and phone numbers:
```bash
python main.py
```
*The data will be saved to `data/crapy_results.csv`.*

### 2. Sync to Flink
To upload the scraped results to your Flink marketplace backend:
```bash
python src/sync_to_flink.py
```
*You will need a valid Flink Bearer Token.*

## Data Output
The CSV contains:
- `product_name`
- `price`
- `location`
- `seller_name`
- `seller_phone`
