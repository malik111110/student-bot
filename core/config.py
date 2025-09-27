import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Core settings
    TELEGRAM_TOKEN: str = "test_token"  # Default for testing
    PROJECT_NAME: str = "Promo Section Bot"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8080
    ENVIRONMENT: str = "development"
    
    # Database settings
    MONGODB_URI: str | None = None
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None  # Added missing field
    
    # External API settings
    PUBLIC_BASE_URL: str | None = None 
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_FALLBACK_MODELS: list[str] = [
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.2-3b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemma-2-9b-it:free"
    ]
    OPENROUTER_SITE_URL: str | None = None
    OPENROUTER_SITE_TITLE: str | None = None
    FIRECRAWL_API_KEY: str | None = None
    ELEVEN_LAB_API_KEY: str | None = None
    
    # Testing settings
    DISABLE_EXTERNAL_CALLS: bool = False
    
    # LLM settings
    LLM_SYSTEM_PROMPT: str = (
        "You are NerdMate, a friendly study companion for Computer Science students. "
        "Be concise, clear, and practical. Use simple language without markdown formatting "
        "(no *, #, **, etc.). Write in plain text with natural paragraphs. "
        "Provide step-by-step guidance and examples. Be encouraging and honest. "
        "If unsure, say so and suggest next steps. Keep responses conversational "
        "and student-friendly, avoiding technical jargon when possible."
    )

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields to be ignored instead of forbidden

def get_settings() -> Settings:
    """Get settings with environment-specific configuration."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "test":
        # Use test-specific env file if it exists
        if os.path.exists(".env.test"):
            return Settings(_env_file=".env.test")
        else:
            # Use test defaults
            return Settings(
                TELEGRAM_TOKEN="test_token",
                FIRECRAWL_API_KEY="test_key",
                ELEVEN_LAB_API_KEY="test_key",
                OPENROUTER_API_KEY="test_key",
                DISABLE_EXTERNAL_CALLS=True,
                ENVIRONMENT="test"
            )
    
    return Settings()

settings = get_settings()
