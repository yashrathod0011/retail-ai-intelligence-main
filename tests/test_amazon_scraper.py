# test_amazon_scraper.py
from src.scrapers.amazon_scraper import AmazonScraper
from src.database.mongo_manager import db_manager
import json

print("Testing Amazon Scraper...\n")

# Initialize scraper
scraper = AmazonScraper()

# Test search
print("🔍 Searching for 'wireless headphones'...")
products = scraper.search_products("wireless headphones", max_results=5)

print(f"\n✅ Found {len(products)} products\n")

# Display results
for i, product in enumerate(products, 1):
    print(f"Product {i}:")
    print(f"  Title: {product['title'][:60]}...")
    print(
        f"  Price: ₹{product['price']}"
        if product["price"]
        else "  Price: Not available"
    )
    print(f"  Rating: {product['rating']}" if product["rating"] else "  Rating: N/A")
    print(f"  ASIN: {product['product_id']}")
    print()

# Save to database
if products:
    print("\n💾 Saving to MongoDB...")
    for product in products:
        product["category"] = "electronics"  # Add category

    ids = db_manager.save_products_bulk(products)
    print(f"✅ Saved {len(ids)} products to database")

    # Verify in database
    saved_products = db_manager.get_products_by_platform("amazon")
    print(f"✅ Total Amazon products in database: {len(saved_products)}")

print("\n🎉 Amazon scraper test complete!")
