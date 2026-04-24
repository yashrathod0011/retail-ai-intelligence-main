# src/agents/analysis_agent.py
from google import genai
from config.settings import settings
from typing import List, Dict
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductAnalysisAgent:
    """AI Agent to analyze scraped product data"""

    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        logger.info("✅ Analysis Agent initialized with Gemini")

    def analyze_products(self, products: List[Dict]) -> Dict:
        """
        Analyze a list of products and generate insights

        Args:
            products: List of product dictionaries from scraper

        Returns:
            Analysis report with insights
        """
        if not products:
            return {"error": "No products to analyze"}

        # Prepare data summary for AI
        products_summary = self._prepare_product_summary(products)

        # Create prompt for AI
        prompt = f"""
You are a retail market analyst. Analyze the following product data and provide actionable insights.

PRODUCT DATA:
{products_summary}

Provide analysis in the following JSON format:
{{
    "total_products": <number>,
    "price_range": {{
        "min": <lowest_price>,
        "max": <highest_price>,
        "average": <average_price>
    }},
    "top_rated_product": {{
        "title": "<product_name>",
        "rating": <rating>,
        "price": <price>
    }},
    "best_value_product": {{
        "title": "<product_name>",
        "reason": "<why_it's_best_value>"
    }},
    "price_insights": [
        "<insight_1>",
        "<insight_2>",
        "<insight_3>"
    ],
    "recommendations": [
        "<recommendation_1>",
        "<recommendation_2>"
    ]
}}

Keep insights concise and actionable. Focus on pricing strategy and competitive positioning.
"""

        logger.info("🤖 Sending data to Gemini for analysis...")

        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash", contents=prompt
            )

            analysis_text = response.text
            analysis = self._extract_json(analysis_text)

            logger.info("✅ Analysis complete!")
            return analysis

        except Exception as e:
            logger.error(f"❌ Error during analysis: {e}")
            return {"error": str(e)}

    def _prepare_product_summary(self, products: List[Dict]) -> str:
        """Convert product list to readable summary - UPDATED FOR NEW SCHEMA"""
        summary_lines = []

        for i, product in enumerate(products, 1):
            # Support both old schema (price) and new schema (current_price)
            price = product.get("current_price") or product.get("price")
            rating = product.get("current_rating") or product.get("rating")
            title = product.get("title", "Unknown")

            line = f"{i}. {title[:60]}... | "
            line += f"₹{price:,.0f}" if price else "Price N/A"
            line += f" | Rating: {rating}" if rating else ""
            line += f" | Trend: {product.get('price_trend', 'N/A')}"
            summary_lines.append(line)

        return "\n".join(summary_lines)

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from AI response (handles markdown code blocks)"""
        try:
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            text = text.strip()
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON, returning raw text")
            return {"raw_response": text}

    def compare_competitors(self, platform_data: Dict[str, List[Dict]]) -> Dict:
        """
        Compare products across different platforms

        Args:
            platform_data: {"amazon": [products], "flipkart": [products]}
        """
        prompt = f"""
Compare products from different e-commerce platforms and provide competitive insights.

DATA:
{json.dumps(platform_data, indent=2)}

Provide comparison in JSON format:
{{
    "platform_summary": {{
        "amazon": {{"avg_price": <price>, "product_count": <count>}},
        "flipkart": {{"avg_price": <price>, "product_count": <count>}}
    }},
    "price_leader": "<platform_with_better_prices>",
    "insights": [
        "<insight_1>",
        "<insight_2>"
    ],
    "recommendations": "<recommendation_for_retailer>"
}}
"""

        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash", contents=prompt
            )
            return self._extract_json(response.text)
        except Exception as e:
            logger.error(f"Error in comparison: {e}")
            return {"error": str(e)}
