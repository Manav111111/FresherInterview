import os
import json
import logging
from typing import Dict, Any, Optional
import jwt
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from app.config import settings

logger = logging.getLogger("fresherai.firebase")

_firebase_initialized = False


def init_firebase():
    """Initializes Firebase Admin SDK if serviceAccountKey.json exists."""
    global _firebase_initialized

    if _firebase_initialized:
        return

    key_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
    if os.path.exists(key_path):
        try:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin SDK initialized with service account key.")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase Admin with key at {key_path}: {e}")

    logger.warning(
        f"Firebase service account key not found at {key_path}. "
        "Running in development fallback mode (unverified token decoding allowed for testing)."
    )


# Attempt initial setup
init_firebase()


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token.
    If Firebase Admin SDK is initialized, uses cryptographically secure verification.
    Otherwise, decodes token payload in development mode.
    """
    if _firebase_initialized:
        try:
            decoded = firebase_auth.verify_id_token(token)
            return {
                "uid": decoded.get("uid"),
                "email": decoded.get("email", ""),
                "name": decoded.get("name", "") or decoded.get("email", "").split("@")[0],
            }
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise ValueError(f"Invalid Firebase ID Token: {e}")

    # Fallback development mode: decode JWT without signature verification
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        uid = decoded.get("user_id") or decoded.get("sub") or decoded.get("uid") or "dev_user_123"
        email = decoded.get("email") or f"{uid}@example.com"
        name = decoded.get("name") or decoded.get("display_name") or email.split("@")[0]
        return {
            "uid": uid,
            "email": email,
            "name": name,
        }
    except Exception:
        # If token is a raw string or test token like 'test-token'
        return {
            "uid": f"test_uid_{hash(token) % 10000}",
            "email": "tester@fresherai.com",
            "name": "Test User",
        }
