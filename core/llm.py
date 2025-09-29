import asyncio
from typing import Any, Dict, List

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - optional dependency for tests
    AsyncOpenAI = None  # type: ignore
from core.config import settings


def _build_client() -> AsyncOpenAI:
    if AsyncOpenAI is None:
        raise RuntimeError("openai package is not installed")
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return AsyncOpenAI(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
    )


async def chat_completion(
    messages: List[Dict[str, str]], model: str | None = None, max_tokens: int = 512
) -> str:
    client = _build_client()
    chosen_model = model or settings.OPENROUTER_MODEL
    headers: Dict[str, str] = {}
    if settings.OPENROUTER_SITE_URL:
        headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
    if settings.OPENROUTER_SITE_TITLE:
        headers["X-Title"] = settings.OPENROUTER_SITE_TITLE

    # Prepend system prompt to keep tone on-brand for Aspire
    system_msg = {"role": "system", "content": settings.LLM_SYSTEM_PROMPT}
    final_messages = [system_msg] + messages

    # Try the chosen model first, then fallback models if it fails
    models_to_try = [chosen_model] + [
        m for m in settings.OPENROUTER_FALLBACK_MODELS if m != chosen_model
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            resp = await client.chat.completions.create(
                model=model_name,
                messages=final_messages,
                max_tokens=max_tokens,
                extra_headers=headers or None,
                extra_body={},
            )
            choice = resp.choices[0]
            if model_name != chosen_model:
                print(f"Successfully used fallback model: {model_name}")
            return choice.message.content or ""
        except Exception as e:
            last_error = e
            print(f"Model {model_name} failed: {e}")
            continue

    # If all models failed, raise the last error
    print(f"All models failed. Last error: {last_error}")
    raise last_error
