# backend/app/schemas.py
from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, Union
from datetime import datetime
from .models import UserRole, BrokerPreference # Import enums from models

# Token Schemas
class Token(BaseModel):
    access_token: str = Field(..., description="JWT Access Token for authenticating requests")
    token_type: str = Field("bearer", description="Type of token (typically 'bearer')")
    refresh_token: Optional[str] = Field(None, description="JWT Refresh Token to obtain a new access token")

class TokenData(BaseModel):
    email: Optional[str] = None
    # sub: Optional[str] = None # 'sub' is a common field for subject/user_id in JWT

# User Base Schemas
class UserBase(BaseModel):
    email: EmailStr
    mobile_number: Optional[constr(min_length=10, max_length=15)] = None
    role: UserRole = UserRole.CLIENT
    broker_preference: Optional[BrokerPreference] = BrokerPreference.NONE

class UserCreate(UserBase):
    password: constr(min_length=8) = Field(..., description="User's password (min 8 characters)")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    mobile_number: Optional[constr(min_length=10, max_length=15)] = None
    broker_preference: Optional[BrokerPreference] = None
    # Add other fields that can be updated by the user

# User Response Schemas
class UserPublic(UserBase):
    id: int
    is_active: bool = True
    is_verified_email: bool = False
    is_verified_mobile: bool = False
    subscription_plan_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # Changed from from_attributes = True for Pydantic v1/v2 compatibility

# Login Schemas
class LoginRequest(BaseModel):
    # User can login with either email or mobile
    username: Union[EmailStr, constr(min_length=10, max_length=15)] # email or mobile
    password: str

# OTP Schemas
class OTPRequest(BaseModel):
    # Send OTP to email or mobile
    identifier: Union[EmailStr, constr(min_length=10, max_length=15)]

class OTPVerify(OTPRequest):
    otp: constr(min_length=4, max_length=8)


# Subscription Plan Schemas (Basic for now)
class SubscriptionPlanBase(BaseModel):
    name: str
    features: Optional[str] = None
    price: int = 0
    duration_days: int = 30

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanPublic(SubscriptionPlanBase):
    id: int
    class Config:
        orm_mode = True


# API Key Schemas (for user to update their broker API keys)
class BrokerAPICredentialsUpdate(BaseModel):
    broker_user_id: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None # For brokers like AngelOne that might provide this after login
    refresh_token: Optional[str] = None # If applicable

    # To make all fields truly optional for partial updates, use Field
    # broker_user_id: Optional[str] = Field(None, description="User's client ID for the broker")
    # api_key: Optional[str] = Field(None, description="Broker API Key")
    # api_secret: Optional[str] = Field(None, description="Broker API Secret")
    # access_token: Optional[str] = Field(None, description="Broker Access Token (if applicable)")
    # refresh_token: Optional[str] = Field(None, description="Broker Refresh Token (if applicable)")
