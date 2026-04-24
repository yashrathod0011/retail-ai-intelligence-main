# src/api/app.py
"""
Flask REST API for Retail Intelligence Platform.
Replaces the Streamlit UI with a proper client-server architecture.
"""
import sys
import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import io

from src.api.chat import chat_bp

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.mongo_manager import db_manager
from src.agents.analysis_agent import ProductAnalysisAgent
from src.utils.pdf_generator import ReportPDFGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App Setup ──────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "..", "ui", "static"),
    static_url_path="/static",
)
CORS(app)

# Singleton instances
_agent = None
_pdf_gen = None

app.register_blueprint(chat_bp)

def get_agent():
    global _agent
    if _agent is None:
        _agent = ProductAnalysisAgent()
    return _agent

def get_pdf_gen():
    global _pdf_gen
    if _pdf_gen is None:
        _pdf_gen = ReportPDFGenerator()
    return _pdf_gen


# ── Helper ─────────────────────────────────────────────────────────────────────
def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    d = dict(doc)
    # Convert ObjectId and datetime
    for key, value in d.items():
        if hasattr(value, '__str__') and type(value).__name__ == 'ObjectId':
            d[key] = str(value)
        elif isinstance(value, datetime):
            d[key] = value.isoformat()
        elif isinstance(value, list):
            d[key] = [serialize_doc(item) if isinstance(item, dict) else
                      (str(item) if type(item).__name__ == 'ObjectId' else
                       (item.isoformat() if isinstance(item, datetime) else item))
                      for item in value]
    return d


# ── Serve Frontend ─────────────────────────────────────────────────────────────
UI_DIR = os.path.join(os.path.dirname(__file__), "..", "ui")

@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/<path:filename>")
def serve_ui_file(filename):
    return send_from_directory(UI_DIR, filename)


# ── Dashboard / Stats ──────────────────────────────────────────────────────────
@app.route("/api/stats")
def get_stats():
    try:
        stats = db_manager.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dashboard/recent")
def get_recent_activity():
    try:
        limit = int(request.args.get("limit", 10))
        products = db_manager.get_all_products(limit=limit)
        data = []
        for p in products:
            data.append({
                "platform": p.get("platform", "N/A").upper(),
                "title": p.get("title", "Unknown"),
                "current_price": p.get("current_price"),
                "price_trend": p.get("price_trend", "stable"),
                "last_seen": p.get("last_seen").isoformat() if isinstance(p.get("last_seen"), datetime) else str(p.get("last_seen", "")),
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Data Collection ────────────────────────────────────────────────────────────
@app.route("/api/collect", methods=["POST"])
def collect_data():
    body = request.get_json() or {}
    search_query = body.get("search_query", "").strip()
    platform = body.get("platform", "amazon").lower()
    category = body.get("category", "electronics").lower()
    max_results = int(body.get("max_results", 10))

    if not search_query:
        return jsonify({"error": "search_query is required"}), 400

    try:
        if platform == "amazon":
            from src.scrapers.amazon_scraper import AmazonScraper
            scraper = AmazonScraper()
        elif platform == "flipkart":
            from src.scrapers.flipkart_scraper import FlipkartScraper
            scraper = FlipkartScraper()

        else:
            return jsonify({"error": f"Unknown platform: {platform}"}), 400

        products = scraper.search_products(search_query, max_results=max_results)

        if not products:
            return jsonify({"error": "No products found", "products": [], "stats": {}}), 200

        for product in products:
            product["category"] = category

        results = db_manager.save_products_bulk(products)

        # Return simplified product list
        simplified = []
        for p in products:
            simplified.append({
                "title": p.get("title", "Unknown"),
                "price": p.get("price"),
                "rating": p.get("rating"),
                "platform": p.get("platform", platform).upper(),
            })

        return jsonify({
            "success": True,
            "stats": results,
            "products": simplified,
            "total": len(products),
        })
    except Exception as e:
        logger.error(f"Collection error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Products ───────────────────────────────────────────────────────────────────
@app.route("/api/products")
def get_products():
    try:
        platform = request.args.get("platform", "all").lower()
        category = request.args.get("category", "all").lower()
        view = request.args.get("view", "all")
        limit = int(request.args.get("limit", 100))

        if view == "price_drops":
            products = db_manager.get_price_drops(min_percent=5.0)
        elif view == "trending":
            products = db_manager.get_trending_products(limit=limit)
        elif platform != "all":
            products = db_manager.get_products_by_platform(platform)
        else:
            products = db_manager.get_all_products(limit=limit)

        if category != "all":
            products = [p for p in products if p.get("category", "").lower() == category]

        return jsonify([serialize_doc(p) for p in products])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/search", methods=["POST"])
def multi_platform_search():
    body = request.get_json() or {}
    search_query = body.get("search_query", "").strip()
    max_results = int(body.get("max_results", 5))
    category = body.get("category", "electronics").lower()
    platforms = body.get("platforms", ["amazon", "flipkart"])

    if not search_query:
        return jsonify({"error": "search_query is required"}), 400

    results = {}
    errors = {}

    for platform in platforms:
        try:
            if platform == "amazon":
                from src.scrapers.amazon_scraper import AmazonScraper
                scraper = AmazonScraper()
            elif platform == "flipkart":
                from src.scrapers.flipkart_scraper import FlipkartScraper
                scraper = FlipkartScraper()

            else:
                continue

            products = scraper.search_products(search_query, max_results)
            if products:
                for p in products:
                    p["category"] = category
                db_manager.save_products_bulk(products)
                results[platform] = [{
                    "title": p.get("title", "Unknown"),
                    "price": p.get("price"),
                    "rating": p.get("rating"),
                    "platform": platform.upper(),
                } for p in products]
        except Exception as e:
            errors[platform] = str(e)

    all_prices = [p["price"] for prods in results.values() for p in prods if p.get("price")]

    return jsonify({
        "results": results,
        "errors": errors,
        "summary": {
            "total": sum(len(v) for v in results.values()),
            "platforms_searched": len(results),
            "min_price": min(all_prices) if all_prices else None,
            "max_price": max(all_prices) if all_prices else None,
            "avg_price": sum(all_prices) / len(all_prices) if all_prices else None,
        }
    })


@app.route("/api/products/price-drops")
def get_price_drops():
    try:
        min_percent = float(request.args.get("min_percent", 10.0))
        products = db_manager.get_price_drops(min_percent=min_percent)
        return jsonify([serialize_doc(p) for p in products])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/price-analytics")
def get_price_analytics():
    try:
        products = db_manager.get_all_products(limit=200)
        prices = [p.get("current_price") for p in products if p.get("current_price") is not None]
        price_increases = [p for p in products if p.get("price_trend") == "up"]

        return jsonify({
            "total_products": len(products),
            "avg_price": sum(prices) / len(prices) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "price_drops_count": sum(1 for p in products if p.get("price_trend") == "down"),
            "price_increases_count": len(price_increases),
            "price_increases": [serialize_doc(p) for p in sorted(price_increases, key=lambda x: x.get("price_change_percent", 0), reverse=True)[:20]],
            "price_distribution": prices[:100],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── AI Analysis ────────────────────────────────────────────────────────────────
@app.route("/api/analysis/quick", methods=["POST"])
def run_quick_analysis():
    body = request.get_json() or {}
    platform = body.get("platform", "all")
    category = body.get("category", "all")

    try:
        query = {}
        if platform != "all":
            query["platform"] = platform.lower()
        if category != "all":
            query["category"] = category.lower()

        products = list(db_manager.products.find(query))

        if not products:
            return jsonify({"error": "No products found for the selected filters"}), 404

        agent = get_agent()
        analysis = agent.analyze_products(products)

        if "error" in analysis:
            return jsonify({"error": analysis["error"]}), 500

        # Save report
        report_data = {
            "report_type": "quick_analysis",
            "platform": platform,
            "category": category,
            "analysis": analysis,
            "products_analyzed": len(products),
        }
        report_id = db_manager.save_report(report_data)

        return jsonify({
            "success": True,
            "report_id": str(report_id),
            "products_analyzed": len(products),
            "analysis": analysis,
        })
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis/deep", methods=["POST"])
def run_deep_analysis():
    body = request.get_json() or {}
    platform = body.get("platform", "all")
    category = body.get("category", "all")

    try:
        from src.agents.crew_manager import crew_manager

        query = {}
        if platform != "all":
            query["platform"] = platform.lower()
        if category != "all":
            query["category"] = category.lower()

        products = list(db_manager.products.find(query))

        if not products:
            return jsonify({"error": "No products found for the selected filters"}), 404

        result = crew_manager.analyze_products(products)

        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        # Save report
        report_data = {
            "report_type": "deep_analysis",
            "platform": platform,
            "category": category,
            "analysis": result,
            "products_analyzed": len(products),
        }
        report_id = db_manager.save_report(report_data)

        return jsonify({
            "success": True,
            "report_id": str(report_id),
            "products_analyzed": len(products),
            "analysis": result,
        })
    except Exception as e:
        logger.error(f"Deep analysis error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Reports ────────────────────────────────────────────────────────────────────
@app.route("/api/reports")
def get_reports():
    try:
        reports = list(db_manager.reports.find(
            {"report_type": {"$in": ["quick_analysis", "deep_analysis"]}}
        ).sort("generated_at", -1).limit(50))
        return jsonify([serialize_doc(r) for r in reports])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/<report_id>/pdf")
def download_report_pdf(report_id):
    try:
        from bson import ObjectId
        report = db_manager.reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            return jsonify({"error": "Report not found"}), 404

        platform_text = report.get("platform", "all").upper()
        category_text = report.get("category", "all").capitalize()

        pdf_gen = get_pdf_gen()
        pdf_bytes = pdf_gen.generate_analysis_report(
            report["analysis"],
            f"{platform_text} - {category_text}",
            products_analyzed=report.get("products_analyzed"),
        )

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"report_{report_id}.pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis/pdf", methods=["POST"])
def download_analysis_pdf():
    body = request.get_json() or {}
    analysis = body.get("analysis")
    label = body.get("label", "Analysis Report")

    if not analysis:
        return jsonify({"error": "analysis data is required"}), 400

    try:
        pdf_gen = get_pdf_gen()
        pdf_bytes = pdf_gen.generate_analysis_report(
            analysis,
            label,
            products_analyzed=body.get("products_analyzed"),
        )

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
