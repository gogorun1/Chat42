from functools import lru_cache

from google import genai

from app.core.config import get_settings
from app.services.gemini_llm_client import GeminiLLMClient


@lru_cache
def get_llm_client() -> GeminiLLMClient:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=settings.gemini_api_key)
    return GeminiLLMClient(client=client, model=settings.gemini_model)
