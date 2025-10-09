import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.blinkit_scraper import BlinkitScraper
from src.scrapers.zepto_scraper import ZeptoScraper
from src.scrapers.bbnow_scraper import BbnowScraper  # Updated from instamart to bbnow
from src.data_manager import DataManager
from config import PLATFORM_URLS

async def run_single_scraper(scraper_class, platform_name, url):
    """Run a single scraper and return its data"""
    print(f"\n Starting {platform_name} scraper...")
    
    try:
        scraper = scraper_class()
        data = await scraper.run_scraper(url)
        print(f" {platform_name}: Successfully scraped {len(data)} products")
        return data
    except Exception as e:
        print(f" {platform_name}: Error - {e}")
        return []

async def main():
    """Run all scrapers and manage data"""
    print("Starting Bread Price Comparison Scraping...")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataManager()
    
    # Define scrapers to run
    scrapers_config = [
        (BlinkitScraper, 'blinkit', PLATFORM_URLS['blinkit']),
        (ZeptoScraper, 'zepto', PLATFORM_URLS['zepto']),
        (BbnowScraper, 'bbnow', PLATFORM_URLS['bbnow'])
    ]
    
    # Run scrapers concurrently for better performance
    tasks = []
    for scraper_class, platform_name, url in scrapers_config:
        task = run_single_scraper(scraper_class, platform_name, url)
        tasks.append(task)
    
    # Wait for all scrapers to complete
    results = await asyncio.gather(*tasks)
    
    # Organize results
    all_platforms_data = {}
    for (scraper_class, platform_name, url), data in zip(scrapers_config, results):
        all_platforms_data[platform_name] = data
        
        # Save individual platform data
        data_manager.save_platform_data(data, platform_name)
    
    # Save combined data
    combined_file = data_manager.save_combined_data(all_platforms_data)
    
    # Convert to DataFrame and save as CSV
    combined_data = data_manager.load_combined_data(combined_file)
    if combined_data:
        df = data_manager.convert_to_dataframe(combined_data)
        if not df.empty:
            csv_file = data_manager.save_dataframe(df)
            
            # Print summary
            print("\n" + "=" * 50)
            print("SCRAPING SUMMARY")
            print("=" * 50)
            total_products = len(df)
            print(f"Total products scraped: {total_products}")
            
            platform_counts = df['platform'].value_counts()
            for platform, count in platform_counts.items():
                print(f"  - {platform}: {count} products")
            
            if 'price_per_100g' in df.columns:
                avg_price = df['price_per_100g'].mean()
                print(f"Average price per 100g: ₹{avg_price:.2f}")
            
            print(f"\n Data saved to:")
            print(f"  - Combined JSON: {combined_file}")
            print(f"  - Analysis CSV: {csv_file}")
    
    return all_platforms_data

if __name__ == "__main__":
    data = asyncio.run(main())