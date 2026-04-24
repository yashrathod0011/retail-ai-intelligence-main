# src/scrapers/amazon_scraper.py
from src.scrapers.base_scraper import BaseScraper
from src.utils.helpers import clean_price, clean_rating, extract_product_id
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    """Scraper specifically for Amazon India"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.amazon.in"
        self.platform = "amazon"

    def search_products(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for products on Amazon

        Args:
            query: Search term (e.g., "samsung phone")
            max_results: How many products to scrape

        Returns:
            List of product dictionaries
        """
        search_url = f"{self.base_url}/s?k={query.replace(' ', '+')}"
        logger.info(f"Searching Amazon for: {query}")

        # Fetch the search results page
        html = self.fetch_with_selenium(search_url)

        if not html:
            logger.error("Failed to fetch Amazon search results")
            return []

        soup = self.parse_html(html)
        products = []

        # Find all product containers
        product_divs = soup.find_all("div", {"data-component-type": "s-search-result"})
        logger.info(f"Found {len(product_divs)} products on page")

        for div in product_divs[:max_results]:
            product = self._extract_product_info(div)
            if product:
                products.append(product)

        logger.info(f"✅ Successfully scraped {len(products)} products")
        return products

    def _extract_product_info(self, product_div) -> Optional[Dict]:
        """Extract information from a single product card - UPDATED FOR NEW SCHEMA"""
        try:
            # Product title
            title_element = product_div.find("h2")
            title = title_element.get_text(strip=True) if title_element else None

            if not title:
                logger.debug("No title found, skipping product")
                return None

            # Product ID (ASIN) - CRITICAL for unique tracking
            asin = product_div.get("data-asin", None)

            if not asin:
                logger.debug("No ASIN found, skipping product")
                return None

            # Price
            price_whole = product_div.find("span", class_="a-price-whole")
            price = None

            if price_whole:
                price_text = price_whole.get_text(strip=True)
                price = clean_price(price_text)

            # Rating
            rating_element = product_div.find("span", class_="a-icon-alt")
            rating = (
                clean_rating(rating_element.get_text(strip=True))
                if rating_element
                else None
            )

            # Number of reviews
            reviews_element = product_div.find(
                "span", {"class": "a-size-base", "dir": "auto"}
            )
            reviews_text = (
                reviews_element.get_text(strip=True) if reviews_element else "0"
            )

            # Product URL
            link_element = (
                product_div.find("h2").find("a") if product_div.find("h2") else None
            )
            url = (
                self.base_url + link_element["href"]
                if link_element and "href" in link_element.attrs
                else None
            )

            # Image
            img_element = product_div.find("img", class_="s-image")
            image_url = (
                img_element["src"]
                if img_element and "src" in img_element.attrs
                else None
            )

            # NEW SCHEMA FORMAT
            product_data = {
                "platform": self.platform,
                "product_id": asin,  # CRITICAL: Unique ID for tracking
                "title": title,
                "price": price,
                "rating": rating,
                "reviews": reviews_text,
                "url": url,
                "image_url": image_url,
                "category": None,  # Will be set when saving
            }

            logger.debug(f"Extracted: {title[:50]}... | ASIN: {asin} | ₹{price}")
            return product_data

        except Exception as e:
            logger.error(f"Error extracting product: {e}")
            return None
