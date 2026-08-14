import logging
from typing import Optional
from langchain_groq import ChatGroq
from app.config import settings

logger = logging.getLogger("fresherai.llm")

_llm_instance: Optional[ChatGroq] = None


def get_llm() -> ChatGroq:
    """Returns a ChatGroq LLM instance for agent workflows."""
    global _llm_instance

    if _llm_instance is not None:
        return _llm_instance

    api_key = settings.GROQ_API_KEY
    if not api_key or "placeholder" in api_key:
        logger.warning("GROQ_API_KEY is not set or contains placeholders. Set GROQ_API_KEY in .env")

    try:
        _llm_instance = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_retries=2,
            api_key=api_key or "gsk_placeholder",
        )
        logger.info(f"Initialized ChatGroq with model {settings.LLM_MODEL}")
    except Exception as e:
        logger.error(f"Failed to initialize ChatGroq: {e}")
        _llm_instance = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            api_key="dummy_key",
        )

    return _llm_instance
