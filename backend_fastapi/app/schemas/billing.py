from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    planId: str = Field(..., description="Selected pricing tier ID, e.g. 'starter', 'pro'")


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OrderResponse(BaseModel):
    success: bool = True
    order: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class VerifyPaymentResponse(BaseModel):
    success: bool = True
    message: str = "Payment successful"
