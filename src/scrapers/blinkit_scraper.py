from .base_scraper import BaseScraper
import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import re

class BlinkitScraper(BaseScraper):
    def __init__(self):
        super().__init__('blinkit')
    
    async def scrape_products(self, page, url):
        try:
            # Navigate to the bread category
            self.logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='load', timeout=50000)

            self.logger.info("Navigated")
            
            # Take initial screenshot for documentation
            await self.take_screenshot(page, "initial_page")
            
            # Wait for products to load
            await page.wait_for_selector('[class*="tw-relative tw-flex"]', timeout=30000)
            
            # Scroll to load all products (important for lazy loading)
            await self._scroll_page(page)
            
            # Extract product information
            products = await page.query_selector_all('[class*="tw-relative tw-flex"]')
            products = products[:self.num_prod]
            self.logger.info(f"Found {len(products)} product elements from BLINKIT")
            
            for i, product in enumerate(products):
                try:
                    product_data = await self._extract_product_data(product)
                    if product_data and self._is_bread_product(product_data):
                        self.data.append(product_data)
                        self.logger.info(f"Extracted: {product_data.get('name', 'Unknown')}")
                    
                    # Take screenshot every 5 products for debugging
                    if i % 5 == 0:
                        await self.take_screenshot(product, f"product_{i}")
                        
                    await self.random_delay()
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting product {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            await self.take_screenshot(page, "unexpected_error")
    
    async def _scroll_page(self, page):
        """Scroll page to load all lazy-loaded content"""
        self.logger.info("Scrolling to load all products...")
        
        scroll_pause = 1
        last_height = await page.evaluate("document.body.scrollHeight")
        
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(scroll_pause)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    async def _extract_product_data(self, product_element):
        """Extract product data from a product element"""
        try:
            # These selectors will need to be customized based on actual Blinkit structure
            # You'll need to inspect the page and update these
            # name_element = await product_element.query_selector('[class*="tw-mb-1.5"]')
            # price_element = await product_element.query_selector('[class*="tw-flex tw-items-center tw-justify-between"]')
            # brand_element = await product_element.query_selector('[class*="Label-sc-15v1nk5-0 BrandName___StyledLabel2-sc-hssfrl-1 gJxZPQ keQNWn"]')
            # weight_element = await product_element.query_selector('[class*="tw-text-200 tw-font-medium tw-line-clamp-1"]')
            
            name_element = await product_element.query_selector('[class*="tw-mb-1.5"]')
            price_element = await product_element.query_selector('[class*="tw-flex tw-items-center tw-justify-between"]')
            # brand_element = await product_element.query_selector('[class*="BrandName"]')
            weight_element = await product_element.query_selector('[class*="tw-text-200 tw-font-medium"]')
            
            name = await name_element.inner_text() if name_element else "Unknown"
            price_text = await price_element.inner_text() if price_element else "0"
            # brand = await brand_element.inner_text() if brand_element else "Unknown"
            weight = await weight_element.inner_text() if weight_element else "Unknown"
            brand = self._extract_brand_from_name(name)
            
            if brand in name:
                name = name.replace(brand, "").strip()
            # Clean price
            price = self._clean_price(price_text)
            weight = self._normalize_weight(weight)
            return {
                'name': name.strip(),
                'brand': brand,
                'weight': weight,
                'price': price,
                'platform': 'blinkit'
            }
            
        except Exception as e:
            self.logger.warning(f"Error extracting product data: {str(e)}")
            return None
        
    def _extract_brand_from_name(self, product_name):
        """Extract brand name from product name"""
        if not product_name or product_name == "Unknown":
            return "Unknown"

        common_brands = [
            'Britannia', 'Modern', 'Harvest Gold', 'English Oven', 
            'The Health Factory', 'Brittania', 'Wibs', 'Perfect Bread',
            'Bonn', 'Fresh', 'Daily', 'Premium','Baker\'s'
        ]

        product_name_lower = product_name.lower()
        for brand in common_brands:
            if brand.lower() in product_name_lower:
                return brand

        # Try to extract first word as brand
        first_word = product_name.split()[0]
        if len(first_word) > 2 and first_word[0].isupper():
            return first_word

        return "Unknown"
        
    def _normalize_weight(self, weight_text: str) -> float:
        try:
            text = weight_text.lower().replace(',', '').strip()
            self.logger.info(text)
            # Extract all numeric values and units (like '2 x 200 g' → ['2', '200'])
            nums = re.findall(r'[\d.]+', text)
            unit = 'g' if 'g' in text else ('kg' if 'kg' in text else ('ml' if 'ml' in text else ''))

            # Convert to grams
            if not nums:
                return 0.0

            if 'x' in text and len(nums) >= 2:
                # Case like "2 x 200 g"
                count = float(nums[0])
                each = float(nums[1])
                total = count * each
            else:
                total = float(nums[-1])  # take last number (like 350 in "1 pack (350 g)")

            if unit == 'kg':
                total *= 1000
            elif unit == 'ml':
                total *= 1  

            return round(total, 2)

        except Exception as e:
            self.logger.warning(f"Weight normalization failed for '{weight_text}': {str(e)}")
            return 0.0
    
    def _clean_price(self, price_text):
        """Extract the correct numeric price (first ₹ value)"""
        try:
            # Match the first ₹number pattern (e.g., ₹59)
            match = re.search(r'₹\s*([\d.,]+)', price_text)
            if match:
                # Clean commas and convert to float
                return float(match.group(1).replace(',', ''))
            return 0.0
        except Exception as e:
            self.logger.warning(f"Price cleaning failed for '{price_text}': {str(e)}")
            return 0.0

    def _is_bread_product(self, product_data):
        """Filter to ensure we only get bread products"""
        name = product_data['name'].lower()
        bread_keywords = ['bread', 'loaf', 'bun', 'pav', 'slice']
        return any(keyword in name for keyword in bread_keywords)


# from .base_scraper import BaseScraper
# import asyncio
# from playwright.async_api import TimeoutError as PlaywrightTimeoutError
# import re
# import random

# class BlinkitScraper(BaseScraper):
#     def __init__(self):
#         super().__init__('blinkit')
    
#     async def scrape_products(self, page, url):
#         try:
#             # Navigate to the bread category
#             self.logger.info(f"Navigating to {url}")
#             await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
#             # Handle potential popups first
#             await self.handle_popups(page)
            
#             self.logger.info("Navigated successfully")
            
#             # Take initial screenshot for documentation
#             await self.take_screenshot(page, "initial_page")
            
#             # Wait for products to load with multiple selector options
#             await self._wait_for_products(page)
            
#             # Scroll to load all products (important for lazy loading)
#             await self._scroll_page(page)
            
#             # Extract product information with multiple selector strategies
#             products = await self._find_product_elements(page)
#             self.logger.info(f"Found {len(products)} product elements")
            
#             for i, product in enumerate(products):
#                 try:
#                     product_data = await self._extract_product_data(product)
#                     if product_data and self._is_bread_product(product_data):
#                         self.data.append(product_data)
#                         self.logger.info(f"Extracted: {product_data.get('name', 'Unknown')} - ₹{product_data.get('price', 0)}")
                    
#                     # Human-like interaction patterns
#                     if i % 3 == 0:  # Reduced frequency for performance
#                         await self.human_like_delay()
                        
#                     # Take screenshot occasionally for debugging
#                     if i % 10 == 0 and i > 0:
#                         await self.take_screenshot(page, f"scrolling_progress_{i}")
                        
#                 except Exception as e:
#                     self.logger.warning(f"Error extracting product {i}: {str(e)}")
#                     continue
                    
#             self.logger.info(f"Successfully extracted {len(self.data)} bread products")
                    
#         except Exception as e:
#             self.logger.error(f"Unexpected error in main scraping: {str(e)}")
#             await self.take_screenshot(page, "main_scraping_error")
    
#     async def _wait_for_products(self, page):
#         """Wait for products to load with multiple fallback selectors"""
#         product_selectors = [
#             '[class*="tw-relative tw-flex"]',
#             '[data-testid*="product"]',
#             '[class*="product-card"]',
#             '[class*="ProductCard"]',
#             '.product-item',
#             '.item-card'
#         ]
        
#         for selector in product_selectors:
#             try:
#                 self.logger.info(f"Trying selector: {selector}")
#                 await page.wait_for_selector(selector, timeout=10000)
#                 self.logger.info(f"Products found using selector: {selector}")
#                 return
#             except Exception as e:
#                 self.logger.debug(f"Selector {selector} failed: {e}")
#                 continue
        
#         # If no selectors work, wait for any product-like elements
#         self.logger.info("Using fallback: waiting for any product elements")
#         await page.wait_for_function(
#             """() => document.querySelectorAll('[class*="product"], [class*="card"], [class*="item"]').length > 0""",
#             timeout=15000
#         )
    
#     async def _find_product_elements(self, page):
#         """Find product elements with multiple selector strategies"""
#         selectors = [
#             '[class*="tw-relative tw-flex"]',
#             '[data-testid*="product"]',
#             '[class*="product-card"]',
#             '.product-item'
#         ]
        
#         all_products = []
#         for selector in selectors:
#             try:
#                 products = await page.query_selector_all(selector)
#                 if products:
#                     self.logger.info(f"Found {len(products)} products with selector: {selector}")
#                     all_products.extend(products)
#             except Exception as e:
#                 self.logger.debug(f"Selector {selector} failed: {e}")
        
#         # Remove duplicates by element handle
#         unique_products = []
#         seen_elements = set()
#         for product in all_products:
#             element_id = await product.evaluate("el => el.outerHTML")
#             if element_id not in seen_elements:
#                 seen_elements.add(element_id)
#                 unique_products.append(product)
        
#         # Limit to reasonable number for performance
#         return unique_products[:30]
    
#     async def _scroll_page(self, page):
#         """Enhanced scrolling with more natural behavior"""
#         self.logger.info("Starting enhanced scrolling...")
        
#         # Random scroll patterns to appear more human
#         scroll_patterns = [
#             (300, 600),   # Small scrolls
#             (600, 900),   # Medium scrolls  
#             (900, 1200),  # Large scrolls
#         ]
        
#         for i in range(5):  # Reduced number of scrolls
#             scroll_min, scroll_max = random.choice(scroll_patterns)
#             scroll_amount = random.randint(scroll_min, scroll_max)
            
#             await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            
#             # Random delay between scrolls
#             delay = random.uniform(0.5, 2)
#             await asyncio.sleep(delay)
            
#             # Occasionally scroll up a bit to mimic human behavior
#             if i % 3 == 0:
#                 await page.evaluate("window.scrollBy(0, -100)")
#                 await asyncio.sleep(0.3)
    
#     async def _extract_product_data(self, product_element):
#         """Enhanced product data extraction with multiple fallbacks"""
#         try:
#             # Try multiple selector patterns for each field
#             name = await self._extract_with_fallback(product_element, 'name', [
#                 '[class*="tw-mb-1.5"]',
#                 '[class*="name"]',
#                 '[class*="title"]',
#                 'h1, h2, h3, h4',
#                 '.product-name'
#             ])
            
#             price_text = await self._extract_with_fallback(product_element, 'price', [
#                 '[class*="tw-flex tw-items-center tw-justify-between"]',
#                 '[class*="price"]',
#                 '[class*="Price"]',
#                 '[class*="amount"]',
#                 '.rupee',
#                 '[class*="currency"]'
#             ])
            
#             weight_text = await self._extract_with_fallback(product_element, 'weight', [
#                 '[class*="tw-text-200 tw-font-medium"]',
#                 '[class*="weight"]',
#                 '[class*="quantity"]',
#                 '[class*="size"]',
#                 '[class*="unit"]'
#             ])
            
#             # Try to extract brand from name as fallback
#             brand = self._extract_brand_from_name(name)
            
#             # Clean and normalize data
#             price = self._clean_price(price_text)
#             weight = self._normalize_weight(weight_text)
            
#             # Validate we have minimum required data
#             if not name or name == "Unknown" or price == 0:
#                 return None
            
#             product_data = {
#                 'name': name.strip(),
#                 'brand': brand,
#                 'weight': weight,
#                 'price': price,
#                 'platform': 'blinkit'
#             }
            
#             self.logger.debug(f"Extracted product: {product_data}")
#             return product_data
            
#         except Exception as e:
#             self.logger.warning(f"Error extracting product data: {str(e)}")
#             return None
    
#     async def _extract_with_fallback(self, element, field_name, selectors):
#         """Extract text with multiple fallback selectors"""
#         for selector in selectors:
#             try:
#                 found_element = await element.query_selector(selector)
#                 if found_element:
#                     text = await found_element.inner_text()
#                     if text and text.strip():
#                         self.logger.debug(f"Found {field_name} with selector: {selector} -> {text.strip()}")
#                         return text.strip()
#             except Exception as e:
#                 self.logger.debug(f"Selector {selector} failed for {field_name}: {e}")
#                 continue
        
#         self.logger.debug(f"No {field_name} found with any selector")
#         return "Unknown"
    
#     def _extract_brand_from_name(self, product_name):
#         """Extract brand name from product name"""
#         if not product_name or product_name == "Unknown":
#             return "Unknown"
            
#         common_brands = [
#             'Britannia', 'Modern', 'Harvest Gold', 'English Oven', 
#             'The Health Factory', 'Brittania', 'Wibs', 'Perfect Bread',
#             'Bonn', 'Fresh', 'Daily', 'Premium'
#         ]
        
#         product_name_lower = product_name.lower()
#         for brand in common_brands:
#             if brand.lower() in product_name_lower:
#                 return brand
        
#         # Try to extract first word as brand
#         first_word = product_name.split()[0]
#         if len(first_word) > 2 and first_word[0].isupper():
#             return first_word
            
#         return "Unknown"
    
#     def _normalize_weight(self, weight_text):
#         """Enhanced weight normalization with better pattern matching"""
#         try:
#             if not weight_text or weight_text == "Unknown":
#                 return 0.0
                
#             text = weight_text.lower().replace(',', '').strip()
#             self.logger.debug(f"Normalizing weight: '{weight_text}' -> '{text}'")
            
#             # Handle different weight patterns
#             patterns = [
#                 # Pattern: "2 x 200 g" or "3x100g"
#                 (r'(\d+)\s*x\s*(\d+)\s*(g|gm|gram|kg|kilo)', self._parse_multipack),
#                 # Pattern: "1 pack (350 g)" or "(500g)"
#                 (r'[\(\[]\s*(\d+)\s*(g|gm|gram|kg|kilo)\s*[\)\]]', self._parse_pack),
#                 # Pattern: "500 g" or "1 kg" or "1.5kg"
#                 (r'(\d+\.?\d*)\s*(g|gm|gram|kg|kilo)', self._parse_simple),
#                 # Pattern: just numbers (assume grams)
#                 (r'^\s*(\d+)\s*$', self._parse_number_only)
#             ]
            
#             for pattern, parser in patterns:
#                 match = re.search(pattern, text)
#                 if match:
#                     result = parser(match)
#                     if result > 0:
#                         self.logger.debug(f"Weight normalized: '{weight_text}' -> {result}g")
#                         return result
            
#             self.logger.warning(f"No weight pattern matched for: '{weight_text}'")
#             return 0.0
            
#         except Exception as e:
#             self.logger.warning(f"Weight normalization failed for '{weight_text}': {str(e)}")
#             return 0.0
    
#     def _parse_multipack(self, match):
#         """Parse multipack weights like '2 x 200 g'"""
#         count = float(match.group(1))
#         each = float(match.group(2))
#         unit = match.group(3)
        
#         total = count * each
#         if unit in ['kg', 'kilo']:
#             total *= 1000
#         return total
    
#     def _parse_pack(self, match):
#         """Parse pack weights like '(500g)' or 'pack of 350g'"""
#         weight = float(match.group(1))
#         unit = match.group(2)
        
#         if unit in ['kg', 'kilo']:
#             weight *= 1000
#         return weight
    
#     def _parse_simple(self, match):
#         """Parse simple weights like '500 g' or '1kg'"""
#         weight = float(match.group(1))
#         unit = match.group(2)
        
#         if unit in ['kg', 'kilo']:
#             weight *= 1000
#         return weight
    
#     def _parse_number_only(self, match):
#         """Parse when only number is found (assume grams)"""
#         return float(match.group(1))
    
#     def _clean_price(self, price_text):
#         """Enhanced price cleaning with multiple pattern support"""
#         try:
#             if not price_text:
#                 return 0.0
                
#             # Multiple price patterns
#             patterns = [
#                 r'₹\s*([\d.,]+)',  # ₹59
#                 r'rs\.?\s*([\d.,]+)',  # Rs. 59 or Rs 59
#                 r'inr\s*([\d.,]+)',  # INR 59
#                 r'([\d.,]+)\s*₹',  # 59 ₹
#                 r'([\d.,]+)\s*$'   # Just numbers at end
#             ]
            
#             for pattern in patterns:
#                 match = re.search(pattern, price_text.lower())
#                 if match:
#                     price_clean = match.group(1).replace(',', '')
#                     price = float(price_clean)
#                     self.logger.debug(f"Price cleaned: '{price_text}' -> ₹{price}")
#                     return price
            
#             self.logger.warning(f"No price pattern matched for: '{price_text}'")
#             return 0.0
            
#         except Exception as e:
#             self.logger.warning(f"Price cleaning failed for '{price_text}': {str(e)}")
#             return 0.0
    
#     def _is_bread_product(self, product_data):
#         """Enhanced bread product filtering"""
#         if not product_data.get('name'):
#             return False
        
#         name = product_data['name'].lower()
        
#         # Bread keywords
#         bread_keywords = [
#             'bread', 'loaf', 'bun', 'pav', 'slice', 'bake', 
#             'brown bread', 'white bread', 'whole wheat', 'atta'
#         ]
        
#         # Non-bread keywords to exclude
#         exclude_keywords = [
#             'jam', 'spread', 'butter', 'cheese', 'toast', 'oven', 'maker',
#             'mix', 'powder', 'yeast', 'pastry', 'cake', 'biscuit', 'cookie'
#         ]
        
#         # Check if it contains bread keywords
#         is_bread = any(keyword in name for keyword in bread_keywords)
        
#         # Check if it should be excluded
#         should_exclude = any(exclude in name for exclude in exclude_keywords)
        
#         result = is_bread and not should_exclude
#         if not result:
#             self.logger.debug(f"Filtered out non-bread product: {name}")
        
#         return result