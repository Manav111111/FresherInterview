import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Cookie, Depends
from app.core.redis import get_cache

logger = logging.getLogger("fresherai.security")


async def get_current_user(
    request: Request,
    session: Optional[str] = Cookie(None),
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and validate the user session from cookies.
    Reads the session UUID from the 'session' cookie and queries Redis cache / local fallback.
    """
    session_id = session or request.cookies.get("session")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: No session cookie provided",
        )

    cached_session = await get_cache(f"session:{session_id}")
    user_data = None

    if cached_session:
        try:
            user_data = json.loads(cached_session)
        except Exception as e:
            logger.warning(f"Error parsing session JSON: {e}")

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
