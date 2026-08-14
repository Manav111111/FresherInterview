import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Cookie, Depends
from app.core.redis import get_redis
from app.core.db import get_supabase

logger = logging.getLogger("fresherai.security")


async def get_current_user(
    request: Request,
    session: Optional[str] = Cookie(None),
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and validate the user session from cookies.
    Reads the session UUID from the 'session' cookie and queries Redis cache.
    Falls back to Supabase DB if Redis key is missing.
    """
    session_id = session or request.cookies.get("session")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: No session cookie provided",
        )

    redis_client = await get_redis()
    user_data = None

    if redis_client:
        try:
            cached_session = await redis_client.get(f"session:{session_id}")
            if cached_session:
                user_data = json.loads(cached_session)
        except Exception as e:
            logger.warning(f"Error reading session from Redis: {e}")

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired or Invalid",
        )

    # Attach user dictionary to request state for easy access
    request.state.user = user_data
    return user_data


async def get_optional_user(
    request: Request,
    session: Optional[str] = Cookie(None),
) -> Optional[Dict[str, Any]]:
    """Optional authentication dependency that does not raise if unauthenticated."""
    try:
        return await get_current_user(request, session)
    except HTTPException:
        return None
