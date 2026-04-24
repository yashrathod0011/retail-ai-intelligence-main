import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def main():
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    print(f"Connecting to MongoDB...")
    
    try:
        client = MongoClient(mongodb_uri)
        db = client["retail_intelligence"]
        reports_collection = db["reports"]
        
        # We only delete the "permanent" reports that show up in the Reports tab
        query = {"report_type": {"$in": ["quick_analysis", "deep_analysis"]}}
        
        count = reports_collection.count_documents(query)
        if count == 0:
            print("No analysis reports found in the database. Nothing to delete.")
            return
            
        print(f"Found {count} analysis reports. Deleting...")
        result = reports_collection.delete_many(query)
        
        print(f"Successfully deleted {result.deleted_count} reports from the database.")
        print("Done. Please refresh the dashboard in your browser.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
