# backend/app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    CLIENT = "client"
    ADMIN = "admin"
    PARTNER = "partner"

class BrokerPreference(str, enum.Enum):
    ANGELONE = "angelone"
    ZERODHA = "zerodha"
    UPSTOX = "upstox"
    NONE = "none" # For users who haven't set a preference or are paper trading only

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    features = Column(String) # Could be JSON or comma-separated
    price = Column(Integer, default=0) # Price in smallest currency unit (e.g., paise)
    duration_days = Column(Integer, default=30) # e.g., 30 for monthly

    users = relationship("User", back_populates="subscription_plan")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile_number = Column(String, unique=True, index=True, nullable=True) # Nullable if signup is email-only first
    password_hash = Column(String, nullable=False)

    role = Column(SAEnum(UserRole), default=UserRole.CLIENT, nullable=False)

    broker_preference = Column(SAEnum(BrokerPreference), default=BrokerPreference.NONE)

    subscription_plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    subscription_plan = relationship("SubscriptionPlan", back_populates="users")

    # Encrypted API credentials
    # Storing them directly in the user table might be okay for now,
    # but for higher security, a separate, more restricted table or a vault service would be better.
    # These will store the encrypted versions of the keys.
    broker_user_id = Column(String, nullable=True) # User ID for the broker (e.g., AngelOne client ID)
    api_key_encrypted = Column(String, nullable=True)
    api_secret_encrypted = Column(String, nullable=True)
    access_token_encrypted = Column(String, nullable=True) # For brokers that use access tokens
    refresh_token_encrypted = Column(String, nullable=True) # For brokers that use refresh tokens

    # OTP related fields
    otp_secret = Column(String, nullable=True) # Secret for generating OTPs (e.g., for 2FA or mobile verification)
    otp_sent_at = Column(DateTime, nullable=True) # Timestamp when the last OTP was sent

    is_active = Column(Boolean, default=True)
    is_verified_email = Column(Boolean, default=False)
    is_verified_mobile = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (if needed later, e.g., trades, journal entries)
    # trades = relationship("Trade", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

# Example: Predefined Subscription Plans (can be inserted via Alembic seed)
# free_plan = SubscriptionPlan(name="Free Tier", features="Basic market data, Paper trading", price=0)
# premium_plan = SubscriptionPlan(name="Premium Trader", features="All features, Real trading, Advanced Analytics", price=99900, duration_days=30)

# You would also need models for:
# - Trades (both paper and real)
# - LearningProgress
# - StrategySettings
# - etc.
# But for now, focusing on the User model and related auth items.
