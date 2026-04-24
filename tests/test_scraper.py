# test_scraper.py
from src.scrapers.base_scraper import BaseScraper

print("Testing Scraper Setup...\n")

scraper = BaseScraper()

# Test fetching a simple page
test_url = "https://www.example.com"

print("Testing with Selenium...")
html = scraper.fetch_with_selenium(test_url)

if html and "Example Domain" in html:
    print("✅ Selenium is working!")
else:
    print("❌ Selenium failed")

print("\n🎉 Scraper base is ready!")
