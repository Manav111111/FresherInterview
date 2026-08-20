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
    FastAPI dependency to extract and validate the user session from Authorization headers or cookies.
    Reads from 'Authorization: Bearer <session_id>', 'x-session-token', or 'session' cookie.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    session_id = None

    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header[7:].strip()
    elif auth_header:
        session_id = auth_header.strip()
    
    if not session_id:
        session_id = request.headers.get("x-session-token")
    if not session_id:
        session_id = session or request.cookies.get("session")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: No session token or cookie provided",
        )

    # Demo session shortcut
    if session_id in ["demo-token", "demo-candidate-token", "test-token"] or session_id.startswith("demo"):
        demo_user = {
            "userId": "demo_candidate_uid",
            "_id": "demo_candidate_uid",
            "id": "demo_candidate_uid",
            "name": "Fresher Candidate",
            "email": "candidate@fresherai.com",
            "interviewCoin": 150,
        }
        request.state.user = demo_user
        return demo_user

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
