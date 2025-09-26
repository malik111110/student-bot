from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    PROJECT_NAME: str = "Promo Section Bot"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8080
    MONGODB_URI: str | None = None
    PUBLIC_BASE_URL: str | None = None  # e.g., https://your.domain.com
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
    LLM_SYSTEM_PROMPT: str = (
        "You are Aspire, a friendly study companion for Computer Science students. "
        "Be concise, clear, and practical. Use simple language without markdown formatting "
        "(no *, #, **, etc.). Write in plain text with natural paragraphs. "
        "Provide step-by-step guidance and examples. Be encouraging and honest. "
        "If unsure, say so and suggest next steps. Keep responses conversational "
        "and student-friendly, avoiding technical jargon when possible."
    )

    class Config:
        env_file = ".env"

settings = Settings()
