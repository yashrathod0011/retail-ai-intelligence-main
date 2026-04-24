# test_scraper_new_schema.py
from src.scrapers.amazon_scraper import AmazonScraper
from src.database.mongo_manager import db_manager

print("Testing Amazon Scraper with NEW Database Schema...\n")
print("=" * 60)

# Initialize scraper
scraper = AmazonScraper()

# Test search
print("🔍 Scraping 5 headphones from Amazon...")
products = scraper.search_products("wireless headphones", max_results=5)

print(f"\n✅ Found {len(products)} products\n")

# Display what we got
print("📦 Scraped Products:")
for i, product in enumerate(products, 1):
    print(f"\n{i}. {product['title'][:60]}...")
    print(f"   ASIN: {product['product_id']}")
    print(f"   Price: ₹{product['price']}" if product["price"] else "   Price: N/A")
    print(
        f"   Rating: {product['rating']}⭐" if product["rating"] else "   Rating: N/A"
    )

# Save to database using NEW upsert method
if products:
    print("\n" + "=" * 60)
    print("💾 Saving to database with NEW schema...\n")

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
    print("🔍 Testing Product Retrieval:")

    # Get first product to show tracking works
    first_product = products[0]
    retrieved = db_manager.get_product_by_id(
        first_product["platform"], first_product["product_id"]
    )

    if retrieved:
        print(f"\n   Product: {retrieved['title'][:50]}...")
        print(f"   Unique ID: {retrieved['unique_id']}")
        print(f"   Current Price: ₹{retrieved['current_price']}")
        print(f"   Price History: {len(retrieved['price_history'])} records")
        print(f"   Times Scraped: {retrieved['times_scraped']}")
        print(f"   First Seen: {retrieved['first_seen']}")
        print(f"   Last Seen: {retrieved['last_seen']}")

print("\n🎉 Test complete!")
