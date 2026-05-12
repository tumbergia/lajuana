from app.core.config import settings
from app.llm.gemini_provider import GeminiProvider


def get_llm_provider() -> GeminiProvider:
    if settings.llm_provider != "gemini":
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

    return GeminiProvider()
