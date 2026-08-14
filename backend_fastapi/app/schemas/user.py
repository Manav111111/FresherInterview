from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    token: str = Field(..., description="Firebase Google OAuth ID token")


class UserSessionData(BaseModel):
    userId: str
    name: Optional[str] = ""
    email: str
    interviewCoin: int = 150


class UserResponse(BaseModel):
    id: str
    firebaseUid: Optional[str] = None
    name: Optional[str] = ""
    email: str
    interviewCoin: int = 150


class UseCoinsRequest(BaseModel):
    coins: int = Field(..., gt=0, description="Amount of interview coins to deduct")
    action: Optional[str] = Field(None, description="Action triggering the coin deduction")


class AddCoinsRequest(BaseModel):
    coins: int = Field(..., gt=0, description="Amount of interview coins to credit")


class AuthResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    user: Optional[Any] = None
    action: Optional[str] = None
    interviewCoin: Optional[int] = None
