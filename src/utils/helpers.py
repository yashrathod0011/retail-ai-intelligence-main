# src/utils/helpers.py
import time
import random
import re
from typing import Optional


def clean_price(price_text):
    """
    Extract numeric price from text

    Args:
        price_text: String containing price (e.g., "₹1,234" or "999.99")

    Returns:
        Float price or None if invalid
    """
    if not price_text:
        return None

    try:
        # Convert to string if not already
        price_str = str(price_text)

        # Remove rupee symbol and whitespace
        price_str = price_str.replace("₹", "").replace("$", "").strip()

        # Check if it's a decimal number (like 999.99)
        if "." in price_str and price_str.count(",") == 0:
            # It's a decimal number, not Indian formatting
            return float(price_str)

        # Remove commas (Indian formatting: 1,23,456 or Western: 123,456)
        price_str = price_str.replace(",", "")

        # Convert to float
        return float(price_str)
    except (ValueError, AttributeError):
        return None


def clean_rating(rating_text: str) -> Optional[float]:
    """Extract numeric rating from text like '4.5 out of 5'"""
    if not rating_text:
        return None

    # Extract first number
    match = re.search(r"(\d+\.?\d*)", rating_text)
    if match:
        return float(match.group(1))
    return None


def random_delay(min_seconds: float = 1, max_seconds: float = 3):
    """Add random delay to avoid being blocked"""
    time.sleep(random.uniform(min_seconds, max_seconds))


def extract_product_id(url: str, platform: str) -> Optional[str]:
    """Extract product ID from URL"""
    if platform == "amazon":
        # Amazon ASIN: /dp/B08N5WRWNW/
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        return match.group(1) if match else None
    elif platform == "flipkart":
        # Flipkart: /product-name/p/itm123
        match = re.search(r"/p/([a-zA-Z0-9]+)", url)
        return match.group(1) if match else None
    return None
