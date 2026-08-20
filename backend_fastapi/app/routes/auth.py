import json
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from app.schemas.user import LoginRequest, UseCoinsRequest, AddCoinsRequest, AuthResponse
from app.utils.firebase_auth import verify_firebase_token
from app.core.db import get_supabase
from app.core.redis import set_cache, delete_cache
from app.core.security import get_current_user

logger = logging.getLogger("fresherai.auth")

auth_router = APIRouter(tags=["Authentication & Coins"])
user_router = APIRouter(tags=["User"])

# In-memory mock database store for development fallback if Supabase is offline
_mock_users_db = {}


@auth_router.post("/login")
async def login(request: Request, body: LoginRequest, response: Response):
    """
    Authenticates a user via Firebase Google OAuth ID Token.
    Upserts user record in Supabase 'users' table, creates Redis session, and sets session cookie.
    """
    try:
        decoded = verify_firebase_token(body.token)
        firebase_uid = decoded["uid"]
        email = decoded["email"]
        name = decoded.get("name", "")

        supabase = get_supabase()
        user_record = None

        # 1. Try querying/upserting user from Supabase
        try:
            res = supabase.table("users").select("*").eq("firebase_uid", firebase_uid).execute()
            if res.data and len(res.data) > 0:
                user_record = res.data[0]
            else:
                # Insert new user with default 150 coins
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
            logger.warning(f"Supabase query failed ({db_err}). Using development user state.")

        # Fallback if DB not reachable
        if not user_record:
            if firebase_uid not in _mock_users_db:
                _mock_users_db[firebase_uid] = {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, firebase_uid)),
                    "firebase_uid": firebase_uid,
                    "email": email,
                    "name": name,
                    "interview_coins": 150,
                }
            user_record = _mock_users_db[firebase_uid]

        user_id = str(user_record.get("id"))
        interview_coin = user_record.get("interview_coins", 150)

        # 2. Create session in Redis / Cache
        session_id = str(uuid.uuid4())
        session_payload = {
            "userId": user_id,
            "_id": user_id,
            "id": user_id,
            "name": user_record.get("name", ""),
            "email": user_record.get("email", ""),
            "interviewCoin": interview_coin,
        }

        await set_cache(
            f"session:{session_id}",
            json.dumps(session_payload),
            ex=60 * 60 * 24 * 7,  # 7 days
        )

        # 3. Set Cookie with protocol detection
        is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        try:
            response.set_cookie(
                key="session",
                value=session_id,
                httponly=True,
                secure=is_https,
                samesite="none" if is_https else "lax",
                max_age=60 * 60 * 24 * 7,
            )
        except Exception:
            pass

        response.headers["x-session-token"] = session_id

        return {
            "success": True,
            "token": session_id,
            "user": session_payload,
        }

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


@auth_router.post("/demo-login")
async def demo_login(request: Request, response: Response):
    """
    Instantly logs in a test candidate for local or demo evaluation without Firebase credentials.
    """
    session_id = f"demo_{uuid.uuid4()}"
    demo_user = {
        "userId": "demo_candidate_uid",
        "_id": "demo_candidate_uid",
        "id": "demo_candidate_uid",
        "name": "Fresher Candidate",
        "email": "candidate@fresherai.com",
        "interviewCoin": 150,
    }

    await set_cache(
        f"session:{session_id}",
        json.dumps(demo_user),
        ex=60 * 60 * 24 * 7,
    )

    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    try:
        response.set_cookie(
            key="session",
            value=session_id,
            httponly=True,
            secure=is_https,
            samesite="none" if is_https else "lax",
            max_age=60 * 60 * 24 * 7,
        )
    except Exception:
        pass

    response.headers["x-session-token"] = session_id

    return {
        "success": True,
        "token": session_id,
        "user": demo_user,
    }


@auth_router.get("/logout")
async def logout(
    request: Request,
    response: Response,
    session: Optional[str] = Cookie(None),
):
    """Logs out the user, removes session from Redis, and clears session cookie."""
    auth_header = request.headers.get("Authorization")
    header_token = auth_header[7:].strip() if auth_header and auth_header.startswith("Bearer ") else None
    session_id = header_token or session or request.cookies.get("session")

    if session_id:
        await delete_cache(f"session:{session_id}")

    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    try:
        response.delete_cookie(
            key="session",
            httponly=True,
            secure=is_https,
            samesite="none" if is_https else "lax",
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": "Logged out successfully",
    }




@auth_router.post("/use-interview-coins")
async def use_interview_coins(
    body: UseCoinsRequest,
    current_user: dict = Depends(get_current_user),
    session: Optional[str] = Cookie(None),
):
    """Deducts interview coins from the current user account."""
    user_id = current_user.get("userId")
    current_coins = current_user.get("interviewCoin", 0)

    if current_coins < body.coins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough interview coins",
        )

    new_coin_balance = current_coins - body.coins

    # Update in Supabase
    supabase = get_supabase()
    try:
        supabase.table("users").update({"interview_coins": new_coin_balance}).eq("id", user_id).execute()
    except Exception as e:
        logger.warning(f"Supabase update failed ({e}). Updating session cache.")

    # Update current session in Redis
    current_user["interviewCoin"] = new_coin_balance
    if session:
        await set_cache(
            f"session:{session}",
            json.dumps(current_user),
            ex=60 * 60 * 24 * 7,
        )

    return {
        "success": True,
        "message": "Interview coins updated successfully",
        "action": body.action,
        "interviewCoin": new_coin_balance,
    }


@auth_router.post("/add-coins")
async def add_coins(
    body: AddCoinsRequest,
    current_user: dict = Depends(get_current_user),
    session: Optional[str] = Cookie(None),
):
    """Credits interview coins to the user account."""
    user_id = current_user.get("userId")
    current_coins = current_user.get("interviewCoin", 0)
    new_coin_balance = current_coins + body.coins

    # Update in Supabase
    supabase = get_supabase()
    try:
        supabase.table("users").update({"interview_coins": new_coin_balance}).eq("id", user_id).execute()
    except Exception as e:
        logger.warning(f"Supabase coin add update failed: {e}")

    # Update session in Redis
    current_user["interviewCoin"] = new_coin_balance
    if session:
        await set_cache(
            f"session:{session}",
            json.dumps(current_user),
            ex=60 * 60 * 24 * 7,
        )

    return {
        "success": True,
        "message": "Coins added successfully",
        "interviewCoin": new_coin_balance,
    }


@user_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns profile and coin data for the currently authenticated user."""
    return {
        "success": True,
        "user": current_user,
    }
