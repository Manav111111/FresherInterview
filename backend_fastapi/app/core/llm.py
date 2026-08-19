import os
import logging
from typing import Optional
from langchain_groq import ChatGroq
from app.config import settings

logger = logging.getLogger("fresherai.llm")

_llm_instance: Optional[ChatGroq] = None


def get_llm() -> ChatGroq:
    """Returns a ChatGroq LLM instance for agent workflows."""
    global _llm_instance

    api_key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
    if not api_key or "placeholder" in api_key:
        logger.warning("GROQ_API_KEY is not set or contains placeholders. Set GROQ_API_KEY in .env")

    model_name = os.getenv("LLM_MODEL") or settings.LLM_MODEL or "openai/gpt-oss-120b"

    if _llm_instance is not None and getattr(_llm_instance, "model_name", "") == model_name:
        return _llm_instance

    try:
        _llm_instance = ChatGroq(
            model=model_name,
            temperature=settings.LLM_TEMPERATURE,
            max_retries=2,
            api_key=api_key or "gsk_placeholder",
        )
        logger.info(f"Initialized ChatGroq with model {model_name}")
    except Exception as e:
        logger.error(f"Failed to initialize ChatGroq with {model_name}: {e}. Trying fallback model.")
        _llm_instance = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.2,
            api_key=api_key or "gsk_placeholder",
        )

    return _llm_instance

