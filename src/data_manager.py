# src/data_manager.py
import json
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

class DataManager:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.base_dir = Path("data")
        self.raw_dir = self.base_dir / "raw"
        self.processed_dir = self.base_dir / "processed"
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def save_platform_data(self, platform_data, platform_name):
        """Save individual platform data to separate file"""
        try:
            filename = self.raw_dir / f"{platform_name}_{self.timestamp}.json"
            
            data_structure = {
                "platform": platform_name,
                "timestamp": datetime.now().isoformat(),
                "scraping_timestamp": self.timestamp,
                "products_count": len(platform_data),
                "products": platform_data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_structure, f, indent=2, ensure_ascii=False)
            
            print(f" {platform_name} data saved: {filename}")
            return filename
            
        except Exception as e:
            print(f" Error saving {platform_name} data: {e}")
            return None
    
    def save_combined_data(self, all_platforms_data):
        """Save all platforms data to a single combined file"""
        try:
            combined_filename = self.raw_dir / f"combined_bread_data_{self.timestamp}.json"
            
            combined_structure = {
                "scraping_session": {
                    "timestamp": datetime.now().isoformat(),
                    "scraping_timestamp": self.timestamp,
                    "total_products": sum(len(data) for data in all_platforms_data.values())
                },
                "platforms": {}
            }
            
            for platform_name, platform_data in all_platforms_data.items():
                combined_structure["platforms"][platform_name] = {
                    "products_count": len(platform_data),
                    "products": platform_data
                }
            
            with open(combined_filename, 'w', encoding='utf-8') as f:
                json.dump(combined_structure, f, indent=2, ensure_ascii=False)
            
            print(f" Combined data saved: {combined_filename}")
            return combined_filename
            
        except Exception as e:
            print(f" Error saving combined data: {e}")
            return None
    
    def load_combined_data(self, filename=None):
        """Load the most recent combined data file"""
        try:
            if filename is None:
                # Find the most recent combined file
                combined_files = list(self.raw_dir.glob("combined_bread_data_*.json"))
                if not combined_files:
                    return None
                filename = max(combined_files, key=os.path.getctime)
            
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f" Error loading combined data: {e}")
            return None
    
    def convert_to_dataframe(self, combined_data):
        """Convert combined JSON data to pandas DataFrame for analysis"""
        try:
            rows = []
            
            for platform_name, platform_info in combined_data["platforms"].items():
                for product in platform_info["products"]:
                    row = product.copy()  # Keep all original fields
                    row['platform'] = platform_name
                    row['scraping_timestamp'] = combined_data["scraping_session"]["scraping_timestamp"]
                    rows.append(row)
            
            df = pd.DataFrame(rows)
            
            # Add price per 100g for better comparison
            if 'weight' in df.columns and 'price' in df.columns:
                df['price_per_100g'] = (df['price'] / df['weight']) * 100
                df['price_per_100g'] = df['price_per_100g'].round(2)
            
            return df
            
        except Exception as e:
            print(f" Error converting to DataFrame: {e}")
            return pd.DataFrame()
    
    def save_dataframe(self, df, filename=None):
        """Save DataFrame to CSV for easy analysis"""
        try:
            if filename is None:
                filename = self.processed_dir / f"bread_prices_analysis_{self.timestamp}.csv"
            
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f" Analysis data saved: {filename}")
            return filename
            
        except Exception as e:
            print(f" Error saving DataFrame: {e}")
            return None