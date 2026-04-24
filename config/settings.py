from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Keys
    groq_api_key: Optional[str] = None
    serpapi_key: Optional[str] = None  # not currently used
    gemini_api_key: str

    # Database
    mongodb_uri: str
    chroma_path: str = "./data/chroma_db"

    # Scraping
    scrape_delay: int = 2
    max_retries: int = 3

    # CrewAI
    crew_llm_model: Optional[str] = "gemini/gemini-2.0-flash"

    class Config:
        env_file = ".env"
        case_sensitive = False


try:
    settings = Settings()

    # Bridge keys into os.environ so CrewAI/litellm can read them
    os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key or "")
    os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key or "")
    os.environ.setdefault("CREW_LLM_MODEL", settings.crew_llm_model or "gemini/gemini-2.0-flash")

    print("✅ Settings loaded successfully!")

except Exception as e:
    print(f"❌ Error loading settings: {e}")
    print("Make sure your .env file has all required keys!")
    raise