# backend/app/schemas.py
from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, Union, List # Added List
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


# Market Data Schemas
class IndexDataPoint(BaseModel):
    symbol: str = Field(..., description="Trading symbol of the index (e.g., ^NSEI, NIFTY 50)")
    ltp: float = Field(..., description="Last Traded Price")
    change: float = Field(..., description="Change in points from previous close")
    percent_change: float = Field(..., alias="percentChange", description="Percentage change from previous close")
    # previous_close: Optional[float] = Field(None, alias="previousClose", description="Previous day's closing price")
    # open_price: Optional[float] = Field(None, alias="openPrice", description="Today's open price")
    # day_high: Optional[float] = Field(None, alias="dayHigh", description="Today's high price")
    # day_low: Optional[float] = Field(None, alias="dayLow", description="Today's low price")
    # volume: Optional[int] = Field(None, description="Trading volume for the day")
    # last_update_timestamp: Optional[datetime] = Field(None, alias="lastUpdateTime", description="Timestamp of the last data update")

    class Config:
        orm_mode = True # For potential future ORM mapping if we store this data
        allow_population_by_field_name = True # Allows using 'percentChange' as input for 'percent_change'

class LiveIndicesResponse(BaseModel):
    data: list[IndexDataPoint]
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the data was fetched/served by the API")


# AngelOne Specific Schemas
class AngelOneFund(BaseModel):
    actid: Optional[str] = None # Account ID, might be same as client code
    amount: Optional[str] = None # String amount, needs conversion to float
    bankactno: Optional[str] = None
    bankid: Optional[str] = None
    bankname: Optional[str] = None
    branchid: Optional[str] = None
    # Add other fund details as per AngelOne API response
    # Example fields often found:
    availablecash: Optional[float] = Field(None, alias="availableCash")
    marginutilized: Optional[float] = Field(None, alias="marginUtilized")
    collateral: Optional[float] = None
    net: Optional[float] = None # Net available margin

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

class AngelOneProfile(BaseModel):
    clientcode: Optional[str] = Field(None, alias="clientCode")
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobileno: Optional[str] = Field(None, alias="mobileNo")
    exchanges: Optional[list[str]] = None # e.g., ["nse", "bse", "mcx"]
    products: Optional[list[str]] = None # e.g., ["CNC", "NRML", "MIS"]
    # lastlogintime: Optional[str] = Field(None, alias="lastLoginTime") # Example
    broker: Optional[str] = Field(None, description="Broker ID/Name, e.g., Angel Broking")
    # funds: Optional[AngelOneFund] = None # If funds are nested under profile

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

# If funds are separate from profile or a more detailed structure:
class AngelOneUserFunds(BaseModel): # More comprehensive fund details
    availablecash: Optional[float] = Field(None, alias="availablecash") # SmartAPI often uses all lowercase
    marginutilized: Optional[float] = Field(None, alias="marginutilized")
    collateral: Optional[float] = Field(None, alias="collateral")
    net: Optional[float] = Field(None, alias="net") # Net available margin
    # Potentially many more fields like payinamount, payoutamount, MTM, unrealizedprofitloss etc.
    # For now, keeping it concise based on common needs.

    class Config:
        allow_population_by_field_name = True # Allow 'availablecash' from API to map to 'availablecash' field
        # orm_mode = True # If this data is ever directly mapped from an ORM model

class AngelOneProfileResponse(BaseModel): # Combining profile and funds for a typical response
    profile: AngelOneProfile
    funds: AngelOneUserFunds # Assuming funds are fetched and combined here

    class Config:
        orm_mode = True


class AngelOneHolding(BaseModel):
    tradingsymbol: Optional[str] = Field(None, alias="tradingSymbol")
    exchange: Optional[str] = None
    isin: Optional[str] = None
    quantity: Optional[int] = None
    averageprice: Optional[float] = Field(None, alias="averagePrice")
    ltp: Optional[float] = None # Last Traded Price
    closeprice: Optional[float] = Field(None, alias="close") # Previous day's close price
    pnl: Optional[float] = Field(None, alias="pnl") # Overall Profit/Loss
    # dayChange: Optional[float] = None # Calculated if needed
    # dayChangePercentage: Optional[float] = None # Calculated if needed
    producttype: Optional[str] = Field(None, alias="productType")
    # Add more fields as per AngelOne API response, e.g., t1quantity, realisedquantity, etc.
    # symboltoken: Optional[str] = Field(None, alias="symbolToken")
    # haircut: Optional[float] = None
    # usedquantity: Optional[int] = Field(None, alias="usedQuantity")
    # collateralquantity: Optional[int] = Field(None, alias="collateralQuantity")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

class AngelOneHoldingsResponse(BaseModel):
    data: Optional[List[AngelOneHolding]] = None # AngelOne might return a list directly under 'data' or just a list

    class Config:
        orm_mode = True
