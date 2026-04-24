# test_flipkart_scraper.py
from src.scrapers.flipkart_scraper import FlipkartScraper
from src.database.mongo_manager import db_manager

print("Testing Flipkart Scraper...\n")
print("=" * 60)

# Initialize scraper
scraper = FlipkartScraper()

# Test search
print("🔍 Scraping 5 headphones from Flipkart...")
products = scraper.search_products("wireless headphones", max_results=5)

print(f"\n✅ Found {len(products)} products\n")

# Display what we got
print("📦 Scraped Products:")
for i, product in enumerate(products, 1):
    print(f"\n{i}. {product['title'][:70]}...")
    print(f"   Product ID: {product['product_id']}")
    print(f"   Price: ₹{product['price']}" if product["price"] else "   Price: N/A")
    print(
        f"   Rating: {product['rating']}⭐" if product["rating"] else "   Rating: N/A"
    )

# Save to database
if products:
    print("\n" + "=" * 60)
    print("💾 Saving to database...\n")

    for product in products:
        product["category"] = "electronics"

    results = db_manager.save_products_bulk(products)

    print(f"📊 Results:")
    print(f"   ✅ New products inserted: {results['inserted']}")
    print(f"   🔄 Existing products updated: {results['updated']}")
    print(f"   ❌ Errors: {results['errors']}")

    print("\n" + "=" * 60)
    print("📈 Database Statistics:")
    stats = db_manager.get_database_stats()
    print(f"   Total Products: {stats['total_products']}")
    print(f"   Platforms: {stats['platforms']}")

    print("\n" + "=" * 60)
    print("🔍 Sample Flipkart Product:")

    first_product = products[0]
    retrieved = db_manager.get_product_by_id(
        first_product["platform"], first_product["product_id"]
    )

    if retrieved:
        print(f"\n   Product: {retrieved['title'][:60]}...")
        print(f"   Unique ID: {retrieved['unique_id']}")
        print(f"   Platform: {retrieved['platform'].upper()}")
        print(f"   Current Price: ₹{retrieved['current_price']}")
        print(f"   Times Scraped: {retrieved['times_scraped']}")

print("\n🎉 Flipkart scraper test complete!")
