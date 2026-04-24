# test_setup.py
print("Testing your complete setup...\n")

# Test 1: Python version
import sys

print(f"✅ Python version: {sys.version}")

# Test 2: Import packages
try:
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
    import chromadb
    from langchain_groq import ChatGroq
    import google.generativeai as genai
    from pymongo import MongoClient

    print("✅ All packages imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")

# Test 3: Load settings
try:
    from config.settings import settings

    print(f"✅ Settings loaded!")
    print(f"   Groq API Key: {'*' * 20}{settings.groq_api_key[-4:]}")
    print(f"   SerpAPI Key: {'*' * 20}{settings.serpapi_key[-4:]}")
    print(f"   Gemini API Key: {'*' * 20}{settings.gemini_api_key[-4:]}")
except Exception as e:
    print(f"❌ Settings error: {e}")

# Test 4: Test Gemini API
try:
    from config.settings import settings

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Say 'Gemini working!' in 3 words")
    print(f"✅ Gemini API working! Response: {response.text}")
except Exception as e:
    print(f"❌ Gemini API error: {e}")

# Test 5: Test MongoDB Atlas
try:
    from pymongo import MongoClient

    client = MongoClient(settings.mongodb_uri)
    client.admin.command("ping")
    print(f"✅ MongoDB Atlas connected!")
except Exception as e:
    print(f"❌ MongoDB error: {e}")

print("\n🎉 Complete setup test finished!")
