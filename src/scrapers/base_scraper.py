import asyncio
import random
import json
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright
import logging
from datetime import datetime
from config import BROWSER_CONFIG
from config import NUMBER_OF_PRODUCTS
class BaseScraper(ABC):
    def __init__(self, platform_name):
        self.platform_name = platform_name
        self.logger = self._setup_logger()
        self.data = []
        self.num_prod = NUMBER_OF_PRODUCTS
        
    def _setup_logger(self):
        logger = logging.getLogger(f"{self.platform_name}_scraper")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    async def random_delay(self):
        """Respectful delay between actions"""
        delay = random.uniform(2, 5)
        self.logger.info(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)
    
    async def take_screenshot(self, page, name):
        """Take screenshot for debugging"""
        screenshot_path = f"debug_{self.platform_name}_{name}_{datetime.now().strftime('%H%M%S')}.png"
        await page.screenshot(path=screenshot_path)
        self.logger.info(f"Screenshot saved: {screenshot_path}")
    
    @abstractmethod
    async def scrape_products(self, url):
        """Main method to implement for each platform"""
        pass
    
    async def run_scraper(self, url):
        """Main method to run the scraper with proper setup"""
        self.logger.info(f"Starting {self.platform_name} scraper...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=BROWSER_CONFIG['headless'],  
                    slow_mo=BROWSER_CONFIG['slow_mo']  
                )
                
                context = await browser.new_context(
                    viewport=BROWSER_CONFIG['viewport'] ,
                    user_agent=BROWSER_CONFIG['user_agent'],
                    ignore_https_errors= BROWSER_CONFIG['ignore_https_errors'],
                    bypass_csp = BROWSER_CONFIG['bypass_csp'],
                )
                
                page = await context.new_page()
                # Implement platform-specific scraping
                await self.scrape_products(page, url)
                
                await browser.close()
                
                self.logger.info(f"Successfully scraped {len(self.data)} products from {self.platform_name}")
                return self.data
                
        except Exception as e:
            self.logger.error(f"Error scraping {self.platform_name}: {str(e)}")
            return []
    
    def save_data(self, filename=None):
        """Save scraped data to JSON"""
        if not filename:
            from config import RAW_DATA_PATH
            filename = RAW_DATA_PATH
            
        with open(filename, 'w') as f:
            json.dump({
                'platform': self.platform_name,
                'timestamp': datetime.now().isoformat(),
                'products': self.data
            }, f, indent=2)
        
        self.logger.info(f"Data saved to {filename}")

# # src/scrapers/base_scraper.py
# import asyncio
# import random
# import json
# from abc import ABC, abstractmethod
# from playwright.async_api import async_playwright
# import logging
# from datetime import datetime
# from config import BROWSER_CONFIG

# class BaseScraper(ABC):
#     def __init__(self, platform_name):
#         self.platform_name = platform_name
#         self.logger = self._setup_logger()
#         self.data = []
        
#     def _setup_logger(self):
#         logger = logging.getLogger(f"{self.platform_name}_scraper")
#         logger.setLevel(logging.INFO)
        
#         if not logger.handlers:
#             handler = logging.StreamHandler()
#             formatter = logging.Formatter(
#                 '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#             )
#             handler.setFormatter(formatter)
#             logger.addHandler(handler)
            
#         return logger
    
#     async def setup_browser_context(self, playwright):
#         """Setup browser with anti-detection measures"""
#         browser = await playwright.chromium.launch(
#             headless=BROWSER_CONFIG['headless'],
#             slow_mo=BROWSER_CONFIG['slow_mo'],
#             args=[
#                 '--disable-blink-features=AutomationControlled',
#                 '--disable-features=VizDisplayCompositor',
#                 '--disable-background-timer-throttling',
#                 '--disable-backgrounding-occluded-windows',
#                 '--disable-renderer-backgrounding',
#                 '--no-first-run',
#                 '--no-default-browser-check',
#                 '--disable-default-apps',
#                 '--disable-translate',
#             ]
#         )
        
#         context = await browser.new_context(
#             viewport=BROWSER_CONFIG['viewport'],
#             user_agent=BROWSER_CONFIG['user_agent'],
#             ignore_https_errors=BROWSER_CONFIG['ignore_https_errors'],
#             bypass_csp=BROWSER_CONFIG['bypass_csp'],
#             java_script_enabled=True,
#         )
        
#         # Add stealth scripts to avoid detection
#         await context.add_init_script("""
#             Object.defineProperty(navigator, 'webdriver', {
#                 get: () => undefined,
#             });
            
#             Object.defineProperty(navigator, 'languages', {
#                 get: () => ['en-US', 'en'],
#             });
            
#             Object.defineProperty(navigator, 'plugins', {
#                 get: () => [1, 2, 3, 4, 5],
#             });
#         """)
        
#         return browser, context
    
#     async def human_like_delay(self):
#         """More human-like random delays"""
#         delay = random.uniform(2, 5)  # Increased delay range
#         self.logger.info(f"Human-like delay: {delay:.2f} seconds")
#         await asyncio.sleep(delay)
    
#     async def take_screenshot(self, page, name):
#         """Take screenshot for debugging"""
#         screenshot_path = f"debug_{self.platform_name}_{name}_{datetime.now().strftime('%H%M%S')}.png"
#         await page.screenshot(path=screenshot_path)
#         self.logger.info(f"Screenshot saved: {screenshot_path}")
    
#     async def handle_popups(self, page):
#         """Handle common popups and overlays"""
#         try:
#             # Try to close common popup selectors
#             popup_selectors = [
#                 '[aria-label="Close"]',
#                 '.close-btn',
#                 '.modal-close',
#                 '[data-testid="close-button"]',
#                 '.popup-close',
#                 'button:has-text("Close")',
#                 'button:has-text("OK")',
#                 'button:has-text("Got it")',
#             ]
            
#             for selector in popup_selectors:
#                 try:
#                     close_btn = await page.query_selector(selector)
#                     if close_btn:
#                         await close_btn.click()
#                         self.logger.info(f"Closed popup with selector: {selector}")
#                         await asyncio.sleep(1)
#                 except:
#                     continue
                    
#         except Exception as e:
#             self.logger.debug(f"No popups to handle: {e}")
    
#     @abstractmethod
#     async def scrape_products(self, page, url):
#         pass
    
#     async def run_scraper(self, url):
#         """Main method to run the scraper with enhanced anti-detection"""
#         self.logger.info(f"Starting {self.platform_name} scraper...")
        
#         try:
#             async with async_playwright() as p:
#                 browser, context = await self.setup_browser_context(p)
#                 page = await context.new_page()
                
#                 # Navigate to URL
#                 self.logger.info(f"Navigating to {url}")
#                 await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
#                 await self.human_like_delay()
                
#                 # Handle any popups
#                 await self.handle_popups(page)
                
#                 # Take initial screenshot
#                 await self.take_screenshot(page, "initial_page")
                
#                 # Implement platform-specific scraping
#                 await self.scrape_products(page, url)
                
#                 await browser.close()
                
#                 self.logger.info(f"Successfully scraped {len(self.data)} products from {self.platform_name}")
#                 return self.data
                
#         except Exception as e:
#             self.logger.error(f"Error scraping {self.platform_name}: {str(e)}")
#             return []