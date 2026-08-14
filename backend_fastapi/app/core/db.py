import logging
from typing import Optional
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger("fresherai.db")

_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """Returns a singleton instance of the Supabase client."""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "placeholder" in settings.SUPABASE_URL:
        logger.warning(
            "Supabase credentials are not configured or contain placeholders. "
            "Please configure SUPABASE_URL and SUPABASE_KEY in .env"
        )

    try:
        url = settings.SUPABASE_URL or "https://placeholder.supabase.co"
        key = settings.SUPABASE_KEY or "placeholder_key"
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        # Return fallback client if possible
        _supabase_client = create_client("https://placeholder.supabase.co", "placeholder_key")

    return _supabase_client
