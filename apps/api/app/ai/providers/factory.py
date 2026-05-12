from app.ai.providers.gemini_provider import GeminiProvider
from app.core.config import settings


def get_llm_provider() -> GeminiProvider:
    if settings.llm_provider != "gemini":
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

    return GeminiProvider()
