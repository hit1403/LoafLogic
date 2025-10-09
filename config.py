# config.py
from datetime import datetime

# Scraping Configuration
REQUEST_DELAY = (2, 5)   # Random delay between requests in seconds
MAX_RETRIES = 3
TIMEOUT = 30000 

BROWSER_CONFIG = {
    'headless': True,  # Set to True after testing
    'slow_mo': 500,  # Slow down interactions (milliseconds)
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'viewport': {'width': 1920, 'height': 1080},
    'ignore_https_errors': True,
    'bypass_csp': True,
}
# Platform URLs (You'll need to find the actual bread category URLs)
PLATFORM_URLS = {
    # 'blinkit': 'https://blinkit.com/cn/bakery-cakes-dairy/bread/p',
    'zepto': 'https://www.zeptonow.com/search?query=bread',
    # 'instamart': 'https://www.swiggy.com/instamart/category-bread-19574',
    'bbnow' : 'https://www.bigbasket.com/ps/?q=breads&nc=as',
    'blinkit': 'https://blinkit.com/s/?q=bread'
}

# Data Files
RAW_DATA_PATH = f"data/raw/bread_data_{datetime.now().strftime('%Y%m%d')}.json"
PROCESSED_DATA_PATH = f"data/processed/compared_prices_{datetime.now().strftime('%Y%m%d')}.csv"
NUMBER_OF_PRODUCTS = 30
# Matching Configuration
FUZZY_MATCH_THRESHOLD = 95  # Percentage for considering products similar