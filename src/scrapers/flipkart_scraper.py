# src/scrapers/flipkart_scraper.py
from src.scrapers.base_scraper import BaseScraper
from src.utils.helpers import clean_price, clean_rating
from typing import List, Dict, Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlipkartScraper(BaseScraper):
    """Scraper specifically for Flipkart India"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.flipkart.com"
        self.platform = "flipkart"

    def search_products(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for products on Flipkart

        Args:
            query: Search term (e.g., "wireless headphones")
            max_results: How many products to scrape

        Returns:
            List of product dictionaries
        """
        search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
        logger.info(f"Searching Flipkart for: {query}")

        # Fetch the search results page
        html = self.fetch_with_selenium(search_url)

        if not html:
            logger.error("Failed to fetch Flipkart search results")
            return []

        soup = self.parse_html(html)
        products = []

        # Find all product containers (using data-id attribute)
        product_divs = soup.find_all("div", {"data-id": True})
        logger.info(f"Found {len(product_divs)} products on page")

        for div in product_divs[:max_results]:
            product = self._extract_product_info(div)
            if product:
                products.append(product)

        logger.info(f"✅ Successfully scraped {len(products)} products")
        return products

    def _extract_product_info(self, product_div) -> Optional[Dict]:
        """Extract information from a single product card using stable structural selectors"""
        try:
            # Product ID from data-id attribute — stable
            product_id = product_div.get("data-id")
            if not product_id:
                return None

            # Product link — find any <a> that contains /p/ in href (stable URL pattern)
            link_element = product_div.find("a", href=re.compile(r"/p/"))
            if not link_element:
                return None

            url = self.base_url + link_element["href"] if link_element.get("href") else None

            # Title — from image alt text (most reliable) or parsed from URL
            title = None
            img_element = product_div.find("img", src=re.compile(r"rukminim|flixcart"))
            if img_element and img_element.get("alt"):
                title = img_element["alt"]

            if not title and url:
                match = re.search(r"/([^/]+)/p/", url)
                if match:
                    title = match.group(1).replace("-", " ").title()

            if not title:
                return None

            image_url = img_element["src"] if img_element and img_element.get("src") else None

            # Price — find text nodes containing ₹ symbol
            price = None
            for tag in product_div.find_all(string=re.compile(r"₹")):
                cleaned = clean_price(tag.strip())
                if cleaned and cleaned > 100:  # ignore delivery charges etc.
                    price = cleaned
                    break

            # Rating — find a tag whose text looks like a rating (e.g. "4.2")
            rating = None
            for tag in product_div.find_all(string=re.compile(r"^\d\.\d$")):
                try:
                    rating = float(tag.strip())
                    break
                except ValueError:
                    continue

            # Reviews — find text like "(1,234)" or "1,234 Ratings"
            reviews = "0"
            reviews_match = product_div.find(
                string=re.compile(r"\d[\d,]+\s*(Ratings|Reviews|ratings|reviews)")
            )
            if reviews_match:
                reviews = reviews_match.strip()

            return {
                "platform": self.platform,
                "product_id": product_id,
                "title": title,
                "price": price,
                "rating": rating,
                "reviews": reviews,
                "url": url,
                "image_url": image_url,
                "category": None,
            }

        except Exception as e:
            logger.error(f"Error extracting product: {e}")
            return None
