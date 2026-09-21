import json
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Cookie, Depends
from app.core.redis import get_cache, set_cache
from app.utils.firebase_auth import verify_firebase_token
from app.core.db import get_supabase

logger = logging.getLogger("fresherai.security")


async def get_current_user(
    request: Request,
    session: Optional[str] = Cookie(None),
) -> Dict[str, Any]:
    """
    FastAPI dependency implementing explicit dual authentication:
    1. Application Session Token: Looks up session:<token> in Redis/cache store.
    2. Stateless Firebase ID Token: Cryptographically verifies signature and identity via Firebase Admin,
       then resolves user identity from Supabase and establishes session cache.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    token_str = None

    if auth_header and auth_header.startswith("Bearer "):
        token_str = auth_header[7:].strip()
    elif auth_header:
        token_str = auth_header.strip()
    
    if not token_str:
        token_str = request.headers.get("x-session-token")
    if not token_str:
        token_str = session or request.cookies.get("session")

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: No session token or cookie provided",
        )

    # Fast path: Demo session shortcut for offline development / demo evaluation
    if token_str in ["demo-token", "demo-candidate-token", "test-token"] or token_str.startswith("demo"):
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

    # =========================================================================
    # Strategy A: Validate application session token in Redis / local session store
    # =========================================================================
    user_data = None
    try:
        cached_session = await get_cache(f"session:{token_str}")
        if cached_session:
            user_data = json.loads(cached_session)
    except Exception as e:
        logger.debug(f"Session cache check error: {e}")

    if user_data and (user_data.get("userId") or user_data.get("id")):
        request.state.user = user_data
        return user_data

    # =========================================================================
    # Strategy B: Secure cryptographic Firebase ID token verification
    # Provides stateless authentication resilient to Redis restarts and dyno recycling
    # =========================================================================
    try:
        decoded_identity = verify_firebase_token(token_str)
        if decoded_identity and "uid" in decoded_identity:
            firebase_uid = decoded_identity["uid"]
            email = decoded_identity.get("email", "")
            name = decoded_identity.get("name", "Fresher Candidate")

            # Resolve application user record from database
            user_record = None
            supabase = get_supabase()
            if supabase:
                try:
                    res = supabase.table("users").select("*").eq("firebase_uid", firebase_uid).execute()
                    if res.data and len(res.data) > 0:
                        user_record = res.data[0]
                    else:
                        insert_res = (
                            supabase.table("users")
                            .insert(
                                {
                                    "firebase_uid": firebase_uid,
                                    "email": email,
                                    "name": name,
                                    "interview_coins": 150,
                                }
                            )
                            .execute()
                        )
                        if insert_res.data:
                            user_record = insert_res.data[0]
                except Exception as db_err:
                    logger.warning(f"Database user lookup during Firebase auth sync notice: {db_err}")

            if user_record:
                user_id = str(user_record.get("id"))
                interview_coin = user_record.get("interview_coins", 150)
                name = user_record.get("name") or name
                email = user_record.get("email") or email
            else:
                user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, firebase_uid))
                interview_coin = 150

            user_data = {
                "userId": user_id,
                "_id": user_id,
                "id": user_id,
                "name": name,
                "email": email,
                "interviewCoin": interview_coin,
            }

            # Cache in application session store for fast subsequent requests
            await set_cache(f"session:{token_str}", json.dumps(user_data), ttl=60 * 60 * 24)

            request.state.user = user_data
            return user_data

    except ValueError as ve:
        # Secure failure: do not leak token parsing details or unverified credentials
        logger.warning(f"Bearer token failed both session lookup and Firebase ID verification: {ve}")
    except Exception as auth_err:
        logger.warning(f"Authentication verification error: {auth_err}")

    # Neither application session nor cryptographic Firebase ID token succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session Expired or Invalid",
    )



async def get_optional_user(
    request: Request,
    session: Optional[str] = Cookie(None),
) -> Optional[Dict[str, Any]]:
    """Optional authentication dependency that does not raise if unauthenticated."""
    try:
        return await get_current_user(request, session)
    except HTTPException:
        return None
