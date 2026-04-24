# src/database/mongo_manager.py
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from typing import List, Dict, Optional
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages all MongoDB operations for retail intelligence"""

    def __init__(self):
        self.client = MongoClient(settings.mongodb_uri)
        self.db = self.client["retail_intelligence"]

        # Collections
        self.products = self.db["products"]
        self.price_history = self.db["price_history"]  # Separate collection for history
        self.reports = self.db["reports"]

        # Create indexes for performance
        self._create_indexes()

        logger.info("✅ MongoDB Manager initialized")

    def _create_indexes(self):
        """Create database indexes for better performance"""
        # Unique index on platform + product_id
        self.products.create_index(
            [("platform", ASCENDING), ("product_id", ASCENDING)],
            unique=True,
            name="unique_product",
        )

        # Index for querying by category and platform
        self.products.create_index([("category", ASCENDING), ("platform", ASCENDING)])

        # Index for price history queries
        self.price_history.create_index(
            [("unique_id", ASCENDING), ("timestamp", DESCENDING)]
        )

        logger.info("✅ Database indexes created")

    def upsert_product(self, product_data: Dict) -> Dict:
        """
        Insert or update a product (intelligent merge)

        Args:
            product_data: Product information from scraper

        Returns:
            Result with action taken (inserted/updated)
        """
        platform = product_data.get("platform")
        product_id = product_data.get("product_id")

        if not platform or not product_id:
            logger.error("Missing platform or product_id")
            return {"error": "Missing required fields"}

        # Create unique identifier
        unique_id = f"{platform}_{product_id}"

        # Check if product exists
        existing = self.products.find_one(
            {"platform": platform, "product_id": product_id}
        )

        timestamp = datetime.now()

        if existing:
            # UPDATE existing product
            result = self._update_existing_product(existing, product_data, timestamp)
            action = "updated"
        else:
            # INSERT new product
            result = self._insert_new_product(product_data, unique_id, timestamp)
            action = "inserted"

        logger.info(f"✅ Product {action}: {product_data.get('title', 'Unknown')[:50]}")
        return {"action": action, "unique_id": unique_id}

    def _insert_new_product(
        self, product_data: Dict, unique_id: str, timestamp: datetime
    ) -> str:
        """Insert a brand new product"""

        # Handle None price values
        price = product_data.get("price")

        new_product = {
            # Unique identifier
            "unique_id": unique_id,
            "platform": product_data.get("platform"),
            "product_id": product_data.get("product_id"),
            # Product info
            "title": product_data.get("title"),
            "category": product_data.get("category", "uncategorized"),
            "url": product_data.get("url"),
            "image_url": product_data.get("image_url"),
            # Current state
            "current_price": price,
            "current_rating": product_data.get("rating"),
            "current_reviews": product_data.get("reviews"),
            "in_stock": True,
            "last_seen": timestamp,
            # Historical tracking
            "first_seen": timestamp,
            "price_history": (
                [{"timestamp": timestamp, "price": price}] if price is not None else []
            ),  # Only add if price exists
            "rating_history": (
                [{"timestamp": timestamp, "rating": product_data.get("rating")}]
                if product_data.get("rating") is not None
                else []
            ),  # Only add if rating exists
            # Computed metrics - handle None values
            "price_trend": "stable",
            "price_change_percent": 0.0,
            "lowest_price": price if price is not None else None,
            "highest_price": price if price is not None else None,
            "average_price": price if price is not None else None,
            "times_scraped": 1,
            # Metadata
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        result = self.products.insert_one(new_product)
        return str(result.inserted_id)

    def _update_existing_product(
        self, existing: Dict, new_data: Dict, timestamp: datetime
    ) -> str:
        """Update an existing product with new scrape data - FIXED for None values"""
        updates = {
            "last_seen": timestamp,
            "updated_at": timestamp,
            "times_scraped": existing.get("times_scraped", 0) + 1,
        }

        # Update current state
        if new_data.get("price") is not None:
            updates["current_price"] = new_data["price"]
        if new_data.get("rating") is not None:
            updates["current_rating"] = new_data["rating"]
        if new_data.get("reviews"):
            updates["current_reviews"] = new_data["reviews"]
        if new_data.get("url"):
            updates["url"] = new_data["url"]

        # Add to price history if price changed
        old_price = existing.get("current_price")
        new_price = new_data.get("price")

        # Only process price updates if new price is not None
        if new_price is not None and old_price != new_price:
            # Add new price point
            price_entry = {"timestamp": timestamp, "price": new_price}
            self.products.update_one(
                {"_id": existing["_id"]}, {"$push": {"price_history": price_entry}}
            )

            # Recalculate price metrics - handle None values safely
            price_history = existing.get("price_history", [])
            all_prices = [
                p["price"] for p in price_history if p.get("price") is not None
            ]
            all_prices.append(new_price)

            # Filter out any None values (just in case)
            all_prices = [p for p in all_prices if p is not None]

            if all_prices:  # Only calculate if we have valid prices
                updates["lowest_price"] = min(all_prices)
                updates["highest_price"] = max(all_prices)
                updates["average_price"] = sum(all_prices) / len(all_prices)

                # Calculate price trend (only if old price exists and is not None)
                if old_price is not None:
                    if new_price < old_price:
                        updates["price_trend"] = "down"
                        updates["price_change_percent"] = (
                            (new_price - old_price) / old_price
                        ) * 100
                    elif new_price > old_price:
                        updates["price_trend"] = "up"
                        updates["price_change_percent"] = (
                            (new_price - old_price) / old_price
                        ) * 100
                    else:
                        updates["price_trend"] = "stable"
                        updates["price_change_percent"] = 0.0

        # Add to rating history if rating changed
        old_rating = existing.get("current_rating")
        new_rating = new_data.get("rating")

        if new_rating is not None and old_rating != new_rating:
            rating_entry = {"timestamp": timestamp, "rating": new_rating}
            self.products.update_one(
                {"_id": existing["_id"]}, {"$push": {"rating_history": rating_entry}}
            )

        # Apply all updates
        self.products.update_one({"_id": existing["_id"]}, {"$set": updates})

        return str(existing["_id"])

    def save_products_bulk(self, products: List[Dict]) -> Dict:
        """
        Save multiple products (uses upsert for each)

        Returns:
            Statistics about the operation
        """
        results = {"inserted": 0, "updated": 0, "errors": 0}

        for product in products:
            try:
                result = self.upsert_product(product)
                if "error" in result:
                    results["errors"] += 1
                elif result["action"] == "inserted":
                    results["inserted"] += 1
                elif result["action"] == "updated":
                    results["updated"] += 1
            except Exception as e:
                logger.error(f"Error upserting product: {e}")
                results["errors"] += 1

        logger.info(
            f"📊 Bulk save: {results['inserted']} new, {results['updated']} updated, {results['errors']} errors"
        )
        return results

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Get all products in a category"""
        products = list(self.products.find({"category": category}))
        return products

    def get_products_by_platform(self, platform: str) -> List[Dict]:
        """Get all products from a platform"""
        products = list(self.products.find({"platform": platform}))
        return products

    def get_product_by_id(self, platform: str, product_id: str) -> Optional[Dict]:
        """Get a specific product"""
        return self.products.find_one({"platform": platform, "product_id": product_id})

    def get_price_drops(self, min_percent: float = 10.0) -> List[Dict]:
        """Get products with recent price drops"""
        products = list(
            self.products.find(
                {"price_trend": "down", "price_change_percent": {"$lt": -min_percent}}
            ).sort("price_change_percent", ASCENDING)
        )
        return products

    def get_trending_products(self, limit: int = 10) -> List[Dict]:
        """Get products with best ratings and recent activity"""
        products = list(
            self.products.find({"current_rating": {"$gte": 4.0}})
            .sort([("current_rating", DESCENDING), ("last_seen", DESCENDING)])
            .limit(limit)
        )
        return products

    def get_all_products(self, limit: int = 100) -> List[Dict]:
        """Get all products with optional limit"""
        products = list(
            self.products.find().sort("updated_at", DESCENDING).limit(limit)
        )
        return products

    def get_database_stats(self) -> Dict:
        """Get statistics about the database"""
        total_products = self.products.count_documents({})
        total_reports = self.reports.count_documents({
            "report_type": {"$in": ["quick_analysis", "deep_analysis"]}
        })

        platforms = self.products.distinct("platform")
        categories = self.products.distinct("category")

        price_drops = self.products.count_documents({"price_trend": "down"})
        price_increases = self.products.count_documents({"price_trend": "up"})

        return {
            "total_products": total_products,
            "total_reports": total_reports,
            "platforms": platforms,
            "categories": categories,
            "price_drops": price_drops,
            "price_increases": price_increases,
        }

    def save_report(self, report_data: Dict) -> str:
        """Save AI-generated analysis report"""
        report_data["generated_at"] = datetime.now()
        result = self.reports.insert_one(report_data)
        logger.info("Report saved to database")
        return str(result.inserted_id)

    def get_latest_report(self, report_type: str = None) -> Optional[Dict]:
        """Get the most recent report"""
        query = {"report_type": report_type} if report_type else {}
        report = self.reports.find_one(query, sort=[("generated_at", DESCENDING)])
        return report

    def clean_database(self):
        """Remove all products (use with caution!)"""
        result = self.products.delete_many({})
        logger.warning(f"⚠️ Deleted {result.deleted_count} products")
        return result.deleted_count

    def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("MongoDB connection closed")


# Global instance
db_manager = MongoDBManager()
