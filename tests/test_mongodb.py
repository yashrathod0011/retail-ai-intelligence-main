# test_mongodb.py
from pymongo import MongoClient
from config.settings import settings

print("Testing MongoDB Atlas connection...\n")

try:
    # Connect to MongoDB Atlas
    client = MongoClient(settings.mongodb_uri)

    # Test connection
    client.admin.command("ping")
    print("✅ Successfully connected to MongoDB Atlas!")

    # Get database
    db = client["retail_intelligence"]
    print(f"✅ Database 'retail_intelligence' ready!")

    # Create a test collection and insert a document
    test_collection = db["test"]
    test_doc = {"message": "Hello from Python!", "status": "working"}
    result = test_collection.insert_one(test_doc)
    print(f"✅ Test document inserted with ID: {result.inserted_id}")

    # Read it back
    retrieved = test_collection.find_one({"message": "Hello from Python!"})
    print(f"✅ Retrieved document: {retrieved}")

    # Clean up test
    test_collection.delete_one({"_id": result.inserted_id})
    print("✅ Test document cleaned up")

    print("\n🎉 MongoDB Atlas is fully configured and working!")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check your MONGODB_URI in .env file")
    print("2. Make sure you replaced <password> with your actual password")
    print("3. Check if IP address is whitelisted in Atlas (0.0.0.0/0)")
    print("4. Make sure database user exists in Atlas")
