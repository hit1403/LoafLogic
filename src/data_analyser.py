# src/data_analyser.py
import pandas as pd
import numpy as np
from thefuzz import fuzz, process
import re
from typing import Dict, List, Tuple
import logging

class DataAnalyser:
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger("data_analyser")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def load_and_preprocess(self, csv_path):
        """Load and preprocess the combined data"""
        self.logger.info(f"Loading data from {csv_path}")
        df = pd.read_csv(csv_path)
        
        df["name"] = df["name"].str.replace(" | Clean Label - Not Brown", "", regex=False)
        df["name"] = df["name"].str.strip()
        
        # Basic cleaning
        df = df.dropna(subset=['name', 'price'])
        df = df[df['price'] > 0] # Remove free products
        df = df[df['weight']>=100] 
        
        # Standardize brand names
        df['brand_standardized'] = df['brand'].apply(self._standardize_brand)
        
        # Extract key product features for matching
        df['product_key'] = df.apply(self._create_product_key, axis=1)
        
        self.logger.info(f"Preprocessed {len(df)} products")
        return df

    def _standardize_brand(self, brand):
        """Standardize brand names"""
        if pd.isna(brand) or brand == "Unknown":
            return "Unknown"
        
        brand = str(brand).upper().strip()
        
        # Common brand variations
        brand_mappings = {
            'BRITANNIA': 'Britannia',
            'MODERN': 'Modern',
            'HARVEST GOLD': 'Harvest Gold',
            'ENGLISH OVEN': 'English Oven',
            'THE HEALTH FACTORY': 'The Health Factory',
            'BRITTANIA': 'Britannia', 
            'WIBs': 'Wibs',
            'BONN': 'Bonn',
            'FRESH': 'Fresh',
            'DAILY': 'Daily'
        }
        
        return brand_mappings.get(brand, brand.title())

    def _create_product_key(self, row):
        """Create a standardized key for product matching"""
        name = str(row['name']).lower()
        brand = str(row['brand_standardized']).lower()
        weight = row['weight']
        
        # Remove common variations
        name = re.sub(r'\b(whole wheat|atta|sliced|fresh|premium)\b', '', name)
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = ' '.join(name.split())  # Normalize whitespace
        # self.logger.info(f"========>{brand}_{name}")
        return f"{brand}_{name}"

    def fuzzy_match_products(self, df, threshold=80):
        """Use fuzzy matching to find identical products across platforms"""
        self.logger.info("Starting fuzzy product matching...")
        
        # Group by product key and find matches
        unique_products = df['product_key'].unique()
        product_groups = {}
        
        for product_key in unique_products:
            # Find similar product keys using fuzzy matching
            matches = process.extract(product_key, unique_products, 
                                    scorer=fuzz.token_sort_ratio, 
                                    limit=10)
            
            # Group products with high similarity
            high_matches = [match[0] for match in matches if match[1] >= threshold]
            
            if high_matches:
                group_key = min(high_matches)  # Use the "smallest" key as group identifier
                if group_key not in product_groups:
                    product_groups[group_key] = []
                product_groups[group_key].extend(high_matches)
        
        # Assign group IDs to each product
        group_mapping = {}
        for group_id, product_keys in enumerate(product_groups.values()):
            for key in product_keys:
                group_mapping[key] = group_id
        
        df['product_group'] = df['product_key'].map(group_mapping)
        
        self.logger.info(f"Created {len(product_groups)} product groups")
        return df

    def generate_insights(self, deals_df):
        """Generate key business insights"""
        insights = {}
        
        # Platform performance
        platform_stats = deals_df.groupby('platform').agg({
            'is_best_deal': 'sum',
            'price_per_100g': 'mean',
            'price_difference_percent': 'mean'
        }).round(2)
        
        insights['platform_performance'] = platform_stats
        
        # Best and worst deals
        best_deals = deals_df[deals_df['is_best_deal'] == True]
        worst_deals = deals_df.nlargest(5, 'price_difference_percent')
        
        insights['best_deals_count'] = best_deals['platform'].value_counts()
        insights['worst_deals'] = worst_deals
        
        # Average price differences
        insights['avg_price_difference'] = deals_df['price_difference_percent'].mean()
        insights['max_savings_opportunity'] = deals_df['savings_opportunity'].max()
        
        return insights

    # In the identify_best_deals method - FIXED VERSION
    def identify_best_deals(self, df):
        """Identify the best deals for each product group - FIXED"""
        self.logger.info("Identifying best deals...")
        
        best_deals = []
        
        for group_id in df['product_group'].unique():
            group_products = df[df['product_group'] == group_id]
            
            # We need at least 2 products from DIFFERENT platforms to compare
            platforms_in_group = group_products['platform'].nunique()
            if platforms_in_group < 2:
                continue  # Skip groups with only one platform
            
            # Find minimum price among available products in this group
            available_products = group_products[group_products['price_per_100g'] > 0]
            if len(available_products) < 2:
                continue
                
            min_price = available_products['price_per_100g'].min()
            
            for _, product in group_products.iterrows():
                # Skip products with no price data
                if product['price_per_100g'] == 0:
                    continue
                    
                price_diff = product['price_per_100g'] - min_price
                price_diff_percent = (price_diff / min_price) * 100 if min_price > 0 else 0
                
                is_best_deal = product['price_per_100g'] == min_price
                
                best_deals.append({
                    'product_group': group_id,
                    'name': product['name'],
                    'brand': product['brand_standardized'],
                    'weight': product['weight'],
                    'price': product['price'],
                    'price_per_100g': product['price_per_100g'],
                    'platform': product['platform'],
                    'is_best_deal': is_best_deal,
                    'price_difference': price_diff,
                    'price_difference_percent': price_diff_percent,
                    'savings_opportunity': price_diff if not is_best_deal else 0
                })
        
        deals_df = pd.DataFrame(best_deals)
        self.logger.info(f"Analyzed {len(deals_df)} product comparisons")
        return deals_df

    
    #issue with the 12.5 and 17.5 issue
    def create_comparison_table(self, deals_df):
        """Create comparison table showing ALL products, with TRUE only for comparable groups"""
        comparison_data = []
        
        # Get ALL product groups (including single-platform ones)
        all_product_groups = deals_df['product_group'].unique()
        
        for group_id in all_product_groups:
            group_products = deals_df[deals_df['product_group'] == group_id]
            # Get product info
            product_name = group_products['name'].mode()[0] if not group_products['name'].mode().empty else group_products.iloc[0]['name']
            brand = group_products['brand'].mode()[0] if not group_products['brand'].mode().empty else group_products.iloc[0]['brand']
            # avg_weight = group_products['weight'].mean()
            
            # Check if this group has multiple platforms (is comparable)
            platforms_present = group_products['platform'].nunique()
            is_comparable = platforms_present >= 2
            
            row = {
                'product_name': product_name,
                'brand': brand,
                'is_comparable': is_comparable,  
                'platforms_available': platforms_present  # Show how many platforms have this
            }
            
            # Initialize all platform columns
            platforms = ['blinkit', 'zepto', 'bbnow']
            for platform in platforms:
                row[f'{platform}_price'] = None
                
                row[f'{platform}_per_100g'] = None
                row[f'{platform}_is_best'] = False
            
            # Find best deal ONLY if group is comparable
            best_deal_platform = None
            if is_comparable:
                best_price_per_100g = float('inf')
                for _, product in group_products.iterrows():
                    
                    price_per_100g = product['price_per_100g']
                    if price_per_100g < best_price_per_100g:
                        best_price_per_100g = price_per_100g
                        best_deal_platform = product['platform']
            
            # Populate platform data
            
            for _, product in group_products.iterrows():
                platform = product['platform']
                if  row[f'{platform}_per_100g'] is not None and product['price_per_100g']<row[f'{platform}_per_100g']:
                    row[f'{platform}_price'] = product['price']
                    row[f'{platform}_per_100g'] = product['price_per_100g']
                elif row[f'{platform}_per_100g'] is None:
                    row[f'{platform}_price'] = product['price']
                    row[f'{platform}_per_100g'] = product['price_per_100g']
                
                # Only mark as best if group is comparable AND this is the best platform
                if is_comparable and platform == best_deal_platform:
                    row[f'{platform}_is_best'] = True
            
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
