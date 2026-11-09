import os
from typing import List
from dotenv import load_dotenv

# Load .env file from backend directory if present
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "LeadPilot AI")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./leadpilot.db")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    LLM_MODEL: str = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
    LLM_EXTRACTION_ENABLED: bool = os.getenv("LLM_EXTRACTION_ENABLED", "false").lower() in ("true", "1", "yes")
    LLM_MAX_CALLS_PER_CONVERSATION: int = int(os.getenv("LLM_MAX_CALLS_PER_CONVERSATION", "2"))
    LLM_MAX_CALLS_PER_DAY: int = int(os.getenv("LLM_MAX_CALLS_PER_DAY", "100"))

    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    WHATSAPP_GRAPH_API_VERSION: str = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v26.0")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
