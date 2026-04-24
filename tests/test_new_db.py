# test_new_db.py
from src.database.mongo_manager import db_manager

print("Testing New Database Manager...\n")

# Test 1: Insert a new product
print("1️⃣ Testing INSERT (new product)...")
test_product = {
    "platform": "amazon",
    "product_id": "TEST123",
    "title": "Test Product - Sony Headphones",
    "price": 10000.0,
    "rating": 4.5,
    "category": "electronics",
}

result1 = db_manager.upsert_product(test_product)
print(f"   Result: {result1}\n")

# Test 2: Update same product with price change
print("2️⃣ Testing UPDATE (price drop)...")
test_product["price"] = 8500.0  # Price dropped!
result2 = db_manager.upsert_product(test_product)
print(f"   Result: {result2}\n")

# Test 3: Retrieve and check price history
print("3️⃣ Checking price history...")
product = db_manager.get_product_by_id("amazon", "TEST123")
print(f"   Current Price: ₹{product['current_price']}")
print(f"   Price Trend: {product['price_trend']}")
print(f"   Price Change: {product['price_change_percent']:.1f}%")
print(f"   Price History: {len(product['price_history'])} records")
for entry in product["price_history"]:
    print(f"      - {entry['timestamp']}: ₹{entry['price']}")
print()

# Test 4: Database stats
print("4️⃣ Database Statistics...")
stats = db_manager.get_database_stats()
print(f"   Total Products: {stats['total_products']}")
print(f"   Platforms: {stats['platforms']}")
print(f"   Price Drops: {stats['price_drops']}")
print(f"   Price Increases: {stats['price_increases']}")

print("\n✅ Database manager test complete!")
