import hmac
import hashlib
import time
import uuid
import logging
from typing import Optional, Dict, Any, List
import razorpay
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.billing import CreateOrderRequest, VerifyPaymentRequest, OrderResponse, VerifyPaymentResponse
from app.core.security import get_current_user
from app.core.db import get_supabase
from app.config import settings

logger = logging.getLogger("fresherai.billing")

billing_router = APIRouter(tags=["Billing & Payments"])

PLANS = {
    "starter": {
        "amount": 199,
        "interviewCoins": 300,
    },
    "pro": {
        "amount": 499,
        "interviewCoins": 1000,
    },
    "enterprise": {
        "amount": 999,
        "interviewCoins": 2500,
    },
}

# In-memory payments fallback for development/testing
_mock_payments_db: Dict[str, Dict[str, Any]] = {}


def _get_razorpay_client() -> Optional[razorpay.Client]:
    """Returns initialized Razorpay SDK client if credentials are configured."""
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET

    if key_id and key_secret and "placeholder" not in key_id and "placeholder" not in key_secret:
        try:
            return razorpay.Client(auth=(key_id, key_secret))
        except Exception as e:
            logger.warning(f"Failed to initialize Razorpay Client: {e}")
    return None


@billing_router.post("/create", status_code=status.HTTP_201_CREATED)
@billing_router.post("/create-order", status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Creates a new Razorpay payment order for the specified coin bundle.
    Logs transaction in Supabase 'payments' table with status 'created'.
    """
    user_id = current_user.get("userId") or current_user.get("id")
    plan_key = body.planId.lower().strip()
    plan = PLANS.get(plan_key)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan '{body.planId}'. Valid plans: {list(PLANS.keys())}",
        )

    rzp_client = _get_razorpay_client()
    order_id = f"order_{uuid.uuid4().hex[:14]}"
    amount_in_paise = plan["amount"] * 100

    if rzp_client:
        try:
            order_data = rzp_client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"rcpt_{int(time.time()*1000)}",
            })
            order_id = order_data.get("id", order_id)
        except Exception as e:
            logger.error(f"Razorpay API order creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment gateway error: {str(e)}",
            )
    else:
        logger.info("Using mock Razorpay order for development/testing.")

    order_payload = {
        "id": order_id,
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"rcpt_{int(time.time()*1000)}",
        "status": "created",
    }

    # Save to Supabase payments table
    db_payload = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "plan_id": plan_key,
        "amount": plan["amount"],
        "interview_coins": plan["interviewCoins"],
        "razorpay_order_id": order_id,
        "status": "created",
    }

    supabase = get_supabase()
    try:
        supabase.table("payments").insert(db_payload).execute()
    except Exception as db_err:
        logger.warning(f"Supabase payment insert failed ({db_err}). Storing in local fallback.")
        _mock_payments_db[order_id] = db_payload

    return {
        "success": True,
        "order": order_payload,
    }


@billing_router.post("/verify")
async def verify_payment(
    body: VerifyPaymentRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Verifies Razorpay HMAC SHA-256 signature and marks transaction as 'paid' in Supabase.
    """
    user_id = current_user.get("userId") or current_user.get("id")
    order_id = body.razorpay_order_id
    payment_id = body.razorpay_payment_id
    signature = body.razorpay_signature

    # 1. Fetch payment record
    supabase = get_supabase()
    payment_record = None

    try:
        res = (
            supabase.table("payments")
            .select("*")
            .eq("razorpay_order_id", order_id)
            .execute()
        )
        if res.data and len(res.data) > 0:
            payment_record = res.data[0]
    except Exception as e:
        logger.warning(f"Supabase query failed: {e}")

    if not payment_record:
        payment_record = _mock_payments_db.get(order_id)

    if not payment_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment transaction not found",
        )

    if payment_record.get("status") == "paid":
        return {
            "success": True,
            "message": "Payment already verified",
        }

    # 2. Verify Razorpay HMAC-SHA256 signature
    key_secret = settings.RAZORPAY_KEY_SECRET
    signature_valid = False

    if key_secret and "placeholder" not in key_secret:
        msg = f"{order_id}|{payment_id}".encode("utf-8")
        generated_signature = hmac.new(
            key_secret.encode("utf-8"),
            msg,
            hashlib.sha256,
        ).hexdigest()

        if generated_signature == signature:
            signature_valid = True
    else:
        # Development fallback test verification
        signature_valid = True

    if not signature_valid:
        # Mark failed
        try:
            supabase.table("payments").update({"status": "failed"}).eq("razorpay_order_id", order_id).execute()
        except Exception:
            pass
        if order_id in _mock_payments_db:
            _mock_payments_db[order_id]["status"] = "failed"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: Invalid signature",
        )

    # 3. Mark paid in database
    update_payload = {
        "status": "paid",
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }

    try:
        supabase.table("payments").update(update_payload).eq("razorpay_order_id", order_id).execute()
    except Exception as e:
        logger.warning(f"Supabase payment update failed: {e}")
        if order_id in _mock_payments_db:
            _mock_payments_db[order_id].update(update_payload)

    return {
        "success": True,
        "message": "Payment successful",
    }


@billing_router.get("/history")
async def get_payment_history(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves payment and coin purchase history for the user."""
    user_id = current_user.get("userId") or current_user.get("id")

    supabase = get_supabase()
    history = []

    try:
        res = (
            supabase.table("payments")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if res.data:
            history = res.data
    except Exception as e:
        logger.warning(f"Supabase payment history query failed: {e}")

    if not history:
        history = [
            p for p in _mock_payments_db.values()
            if str(p.get("user_id")) == str(user_id)
        ]

    return {
        "success": True,
        "history": history,
    }
