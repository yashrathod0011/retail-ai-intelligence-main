# test_ai_agent.py
from src.database.mongo_manager import db_manager
from src.agents.analysis_agent import ProductAnalysisAgent
import json

print("Testing AI Analysis Agent...\n")

# Step 1: Get products from database
print("📊 Fetching products from MongoDB...")
products = db_manager.get_products_by_platform('amazon')

if not products:
    print("❌ No products found in database!")
    print("   Run: python test_amazon_scraper.py first")
    exit()

print(f"✅ Found {len(products)} products in database\n")

# Step 2: Initialize AI Agent
print("🤖 Initializing AI Agent...")
agent = ProductAnalysisAgent()

# Step 3: Analyze products
print("🔍 Analyzing products with Gemini AI...\n")
analysis = agent.analyze_products(products)

# Step 4: Display results
print("="*60)
print("📈 ANALYSIS REPORT")
print("="*60)
print(json.dumps(analysis, indent=2))
print("="*60)

# Step 5: Save report to database
print("\n💾 Saving report to MongoDB...")
report_data = {
    'report_type': 'product_analysis',
    'platform': 'amazon',
    'category': 'electronics',
    'analysis': analysis,
    'products_analyzed': len(products)
}

report_id = db_manager.save_report(report_data)
print(f"✅ Report saved with ID: {report_id}")

print("\n🎉 AI Agent test complete!")