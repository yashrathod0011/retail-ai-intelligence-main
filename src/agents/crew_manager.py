from crewai import Agent, Task, Crew, Process
from typing import List, Dict
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetailIntelligenceCrew:

    def __init__(self):
        self.model = "groq/llama-3.1-8b-instant"
        logger.info(f"🤖 Crew using model: {self.model}")

    def create_agents(self) -> Dict[str, Agent]:

        data_scout = Agent(
            role="Data Scout",
            goal="Identify trending products, market gaps, and competitive patterns",
            backstory=(
                "You are an expert market researcher with deep experience in "
                "e-commerce trends, consumer behavior, and competitive analysis."
            ),
            llm=self.model,
            verbose=False,
            allow_delegation=False,
            max_iter=2,
        )

        pricing_analyst = Agent(
            role="Pricing Strategist",
            goal="Analyze pricing patterns and recommend optimal pricing strategies",
            backstory=(
                "You are a pricing expert who understands margins, elasticity, "
                "and competitive positioning in retail markets."
            ),
            llm=self.model,
            verbose=False,
            allow_delegation=False,
            max_iter=2,
        )

        risk_assessor = Agent(
            role="Risk Assessment Specialist",
            goal="Identify market, pricing, and competitive risks",
            backstory=(
                "You are a retail risk analyst skilled at identifying saturation, "
                "pricing wars, and structural weaknesses before they escalate."
            ),
            llm=self.model,
            verbose=False,
            allow_delegation=False,
            max_iter=2,
        )

        report_writer = Agent(
            role="Strategic Report Writer",
            goal="Synthesize insights into clear, actionable business recommendations",
            backstory=(
                "You are a consultant who converts complex analysis into "
                "executive-ready insights and action plans."
            ),
            llm=self.model,
            verbose=False,
            allow_delegation=False,
            max_iter=2,
        )

        return {
            "scout": data_scout,
            "pricing": pricing_analyst,
            "risk": risk_assessor,
            "writer": report_writer,
        }

    def create_tasks(self, agents: Dict[str, Agent], products_data: str) -> List[Task]:

        scout_task = Task(
            description=f"""
Analyze the product data and identify:
- Emerging product categories and trends
- Common traits of high-performing products
- Market gaps or opportunities

PRODUCT DATA:
{products_data}
""",
            agent=agents["scout"],
            expected_output="A concise bullet-point market trends and opportunity analysis.",
        )

        pricing_task = Task(
            description=f"""
Analyze pricing across the products:
- Identify overpriced and underpriced items
- Recommend specific pricing adjustments
- Explain the rationale clearly

PRODUCT DATA:
{products_data}
""",
            agent=agents["pricing"],
            expected_output="Pricing recommendations with clear justification for each.",
        )

        risk_task = Task(
            description=f"""
Identify risks in the current product portfolio:
- Market saturation risks
- Competitive threats
- Pricing pressure points

PRODUCT DATA:
{products_data}
""",
            agent=agents["risk"],
            expected_output="A prioritized list of risks with mitigation strategies.",
        )

        writer_task = Task(
            description=f"""
Write a concise executive report covering:
- 3 key market insights
- Top 5 actionable recommendations
- 30-day and 90-day action plan

Use this product data as context:
{products_data}
""",
            agent=agents["writer"],
            expected_output="A structured executive report ready for business review.",
        )

        return [scout_task, pricing_task, risk_task, writer_task]

    def analyze_products(self, products: List[Dict]) -> Dict:
        logger.info("⚙️ Initializing crew and tasks...")

        if not products:
            return {"error": "No products provided for analysis"}

        products_summary = self._prepare_product_summary(products)
        agents = self.create_agents()
        tasks = self.create_tasks(agents, products_summary)

        try:
            results = []

            for i, task in enumerate(tasks):
                logger.info(f"📋 Running task {i+1}/{len(tasks)}: {task.agent.role}")

                mini_crew = Crew(
                    agents=[task.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False,
                )

                task_result = mini_crew.kickoff()
                output = task_result.raw if hasattr(task_result, "raw") else str(task_result)

                results.append({
                    "agent": task.agent.role,
                    "output": output,
                })

                logger.info(f"✅ Task {i+1}/{len(tasks)} complete")

                if i < len(tasks) - 1:
                    logger.info(f"⏳ Waiting 60 seconds before next task...")
                    time.sleep(60)

            final_report = results[-1]["output"] if results else "No results generated"
            logger.info("✅ All tasks completed successfully")

            return {
                "final_report": final_report,
                "detailed_results": results,
                "tasks_completed": len(results),
                "model_used": self.model,
            }

        except Exception as e:
            logger.error(f"❌ Crew execution failed: {e}")
            error_msg = str(e)
            if "rate" in error_msg.lower() or "429" in error_msg:
                return {
                    "error": (
                        "Groq rate limit hit. Wait a minute and try again."
                    )
                }
            if "auth" in error_msg.lower() or "401" in error_msg or "api key" in error_msg.lower():
                return {
                    "error": (
                        "Authentication failed. Check that GROQ_API_KEY is "
                        "correct in your .env file."
                    )
                }
            return {"error": error_msg}

    def _prepare_product_summary(self, products: List[Dict]) -> str:
        lines = []
        for i, product in enumerate(products[:20]):
            line = f"{i+1}. {product.get('title', 'Untitled')}"
            price = product.get("current_price") or product.get("price")
            rating = product.get("current_rating") or product.get("rating")
            if price:
                line += f" | ₹{price:,.0f}"
            if rating:
                line += f" | {rating}⭐"
            if product.get("platform"):
                line += f" | [{product['platform'].upper()}]"
            line += f" | Trend: {product.get('price_trend', 'N/A')}"
            lines.append(line)

        if len(products) > 20:
            lines.append(f"... and {len(products) - 20} more products")

        return "\n".join(lines)


# Global instance
crew_manager = RetailIntelligenceCrew()