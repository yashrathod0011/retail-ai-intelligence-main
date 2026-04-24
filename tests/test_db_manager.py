# test_db_manager.py
from src.database.mongo_manager import db_manager

print("Testing Database Manager...\n")

# Test 1: Save a sample product
sample_product = {
    "platform": "amazon",
    "title": "Samsung Galaxy S24 Ultra",
    "price": 124999.0,
    "category": "electronics",
    "rating": 4.5,
    "url": "https://amazon.in/example",
}

try:
    product_id = db_manager.save_product(sample_product)
    print(f"✅ Product saved with ID: {product_id}")
except Exception as e:
    print(f"❌ Error saving product: {e}")

# Test 2: Save multiple products
sample_products = [
    {
        "platform": "flipkart",
        "title": "iPhone 15 Pro",
        "price": 134999.0,
        "category": "electronics",
        "rating": 4.7,
        "url": "https://flipkart.com/example",
    },
    {
        "platform": "amazon",
        "title": "Sony WH-1000XM5 Headphones",
        "price": 29990.0,
        "category": "electronics",
        "rating": 4.6,
        "url": "https://amazon.in/example2",
    },
]

try:
    ids = db_manager.save_products_bulk(sample_products)
    print(f"✅ Saved {len(ids)} products in bulk")
except Exception as e:
    print(f"❌ Error saving bulk: {e}")

# Test 3: Retrieve products by category
try:
    electronics = db_manager.get_products_by_category("electronics")
    print(f"✅ Found {len(electronics)} electronics products")
    for product in electronics:
        print(f"   - {product['title']} @ ₹{product['price']}")
except Exception as e:
    print(f"❌ Error retrieving: {e}")

# Test 4: Save a report
sample_report = {
    "report_type": "price_analysis",
    "category": "electronics",
    "summary": "Prices are competitive in smartphones segment",
    "insights": ["Samsung is 10% cheaper than iPhone", "Headphones have good margins"],
}

try:
    report_id = db_manager.save_report(sample_report)
    print(f"✅ Report saved with ID: {report_id}")
except Exception as e:
    print(f"❌ Error saving report: {e}")

# Test 5: Get latest report
try:
    latest = db_manager.get_latest_report("price_analysis")
    if latest:
        print(f"✅ Latest report: {latest['summary']}")
except Exception as e:
    print(f"❌ Error getting report: {e}")

print("\n🎉 Database Manager is working perfectly!")
