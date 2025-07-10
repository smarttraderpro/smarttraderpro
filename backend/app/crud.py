# backend/app/crud.py
from sqlalchemy.orm import Session
from typing import Optional, Union

from . import models, schemas
from backend.core.security import get_password_hash, verify_password # verify_password was unused, but good to keep for now

# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_mobile(db: Session, mobile_number: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.mobile_number == mobile_number).first()

def get_user_by_email_or_mobile(db: Session, identifier: Union[str, int]) -> Optional[models.User]:
    """
    Retrieves a user by email or mobile number.
    Assumes identifier is a string.
    """
    if "@" in str(identifier): # Basic check for email
        return get_user_by_email(db, str(identifier))
    else:
        return get_user_by_mobile(db, str(identifier))


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        mobile_number=user.mobile_number,
        password_hash=hashed_password,
        role=user.role,
        broker_preference=user.broker_preference,
        # Explicitly set new user status, overriding model defaults if necessary
        is_active=False,
        is_verified_email=False,
        is_verified_mobile=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(
    db: Session,
    db_user: models.User,
    user_in: Union[schemas.UserUpdate, schemas.BrokerAPICredentialsUpdate],
    original_email: Optional[str] = None,
    original_mobile_number: Optional[str] = None
) -> models.User:
    user_data = user_in.model_dump(exclude_unset=True)

    new_email = user_data.get("email")
    new_mobile_number = user_data.get("mobile_number")

    for key, value in user_data.items():
        if key not in ['api_key', 'api_secret', 'access_token', 'refresh_token']:
            setattr(db_user, key, value)

    from backend.core.security import encrypt_data
    if 'api_key' in user_data: # Handles both value and None
        db_user.api_key_encrypted = encrypt_data(user_data.pop('api_key'))
    if 'api_secret' in user_data:
        db_user.api_secret_encrypted = encrypt_data(user_data.pop('api_secret'))
    if 'access_token' in user_data:
        db_user.access_token_encrypted = encrypt_data(user_data.pop('access_token'))
    if 'refresh_token' in user_data:
        db_user.refresh_token_encrypted = encrypt_data(user_data.pop('refresh_token'))

    if original_email is not None and new_email is not None and new_email != original_email:
        db_user.is_verified_email = False

    if original_mobile_number is not None and new_mobile_number is not None and new_mobile_number != original_mobile_number:
        db_user.is_verified_mobile = False
    elif original_mobile_number is None and new_mobile_number is not None: # Adding mobile for the first time
        db_user.is_verified_mobile = False

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: Union[str, int], password: str) -> Optional[models.User]:
    user = get_user_by_email_or_mobile(db, username)
    if not user:
        return None
    # Removed: if not user.is_active: return None
    # The endpoint /auth/login will handle the is_active check to give a specific response.
    if not verify_password(password, user.password_hash):
        return None
    return user


# OTP Management for User
def set_user_otp(db: Session, user: models.User, otp: str) -> models.User:
    from datetime import datetime, timezone
    user.otp_secret = otp
    user.otp_sent_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def clear_user_otp(db: Session, user: models.User) -> models.User:
    user.otp_secret = None
    user.otp_sent_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user_email(db: Session, user: models.User) -> models.User: # Kept for direct use if needed
    user.is_verified_email = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user_mobile(db: Session, user: models.User) -> models.User:
    user.is_verified_mobile = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def activate_user_and_verify_email(db: Session, user: models.User) -> models.User:
    user.is_verified_email = True
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Subscription Plan CRUD
def get_subscription_plan(db: Session, plan_id: int) -> Optional[models.SubscriptionPlan]:
    return db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == plan_id).first()

def get_subscription_plan_by_name(db: Session, name: str) -> Optional[models.SubscriptionPlan]:
    return db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.name == name).first()

def create_subscription_plan(db: Session, plan: schemas.SubscriptionPlanCreate) -> models.SubscriptionPlan:
    db_plan = models.SubscriptionPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan
