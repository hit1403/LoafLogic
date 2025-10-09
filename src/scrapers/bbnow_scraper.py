from .base_scraper import BaseScraper
import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import re

class BbnowScraper(BaseScraper):
    def __init__(self):
        super().__init__('bbnow')
    
    async def scrape_products(self, page, url):
        try:
            # Navigate to the bread category
            self.logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='load', timeout=50000)

            self.logger.info("Navigated")
            
            # Take initial screenshot for documentation
            await self.take_screenshot(page, "initial_page")
            
            # Wait for products to load
            await page.wait_for_selector('[class*="PaginateItems"]', timeout=30000)
            
            # Scroll to load all products (important for lazy loading)
            await self._scroll_page(page)
            
            # Extract product information
            products = await page.query_selector_all('[class*="PaginateItems"]')
            products = products[:self.num_prod]
            self.logger.info(f"Found {len(products)} product elements from BBNOW")
            
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
                    
        # except PlaywrightTimeoutError:
        #     self.logger.error("Timeout waiting for products to load")
        #     await self.take_screenshot(page, "timeout_error")
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
            # name_element = await product_element.query_selector('[class*="break-words h-10 w-full"]')
            # price_element = await product_element.query_selector('[class*="Pricing___StyledDiv-sc-pldi2d-0 bUnUzR"]')
            # brand_element = await product_element.query_selector('[class*="Label-sc-15v1nk5-0 BrandName___StyledLabel2-sc-hssfrl-1 gJxZPQ keQNWn"]')
            # weight_element = await product_element.query_selector('[class*="py-1.5 xl:py-1"]')
            
            name_element = await product_element.query_selector('[class*="break-words"]')
            price_element = await product_element.query_selector('[class*="Pricing"]')
            brand_element = await product_element.query_selector('[class*="BrandName"]')
            weight_element = await product_element.query_selector('[class*="py-1.5"]')
            
            name = await name_element.inner_text() if name_element else "Unknown"
            price_text = await price_element.inner_text() if price_element else "0"
            brand = await brand_element.inner_text() if brand_element else "Unknown"
            weight = await weight_element.inner_text() if weight_element else "Unknown"
            
            # Clean price
            price = self._clean_price(price_text)
            weight = self._normalize_weight(weight)
            return {
                'name': name.strip(),
                'brand': brand.strip(),
                'weight': weight,
                'price': price,
                'platform': 'bbnow'
            }
            
        except Exception as e:
            self.logger.warning(f"Error extracting product data: {str(e)}")
            return None
        
    def _normalize_weight(self, weight_text: str) -> float:
        """
        Convert weight text into numeric grams.
        Examples:
            "1 pack (350 g)" -> 350
            "2 x 200 g" -> 400
            "1 kg" -> 1000
            "500 g" -> 500
            "1.5 kg" -> 1500
        """
        try:
            text = weight_text.lower().replace(',', '').strip()

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
                total *= 1  # keep ml as-is, unless you want to convert later

            return round(total, 2)

        except Exception as e:
            self.logger.warning(f"Weight normalization failed for '{weight_text}': {str(e)}")
            return 0.0
    
    # def _clean_price(self, price_text):
    #     """Extract numeric price from text"""
    #     try:
    #         # Remove currency symbols and commas, then convert to float
    #         price_clean = re.sub(r'[^\d.]', '', price_text)
    #         return float(price_clean)
    #     except:
    #         return 0.0
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