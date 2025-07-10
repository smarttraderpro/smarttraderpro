# backend/app/crud.py
from sqlalchemy.orm import Session
from typing import Optional, Union

from . import models, schemas
from backend.core.security import get_password_hash, verify_password

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
        role=user.role, # Role comes from UserCreate, defaults to CLIENT if not provided
        broker_preference=user.broker_preference # Defaults to NONE if not provided
        # is_active can be True by default, or False until email verification
    ) # Correctly close the User constructor here
    # By default, email and mobile are not verified
    db_user.is_verified_email = False
    db_user.is_verified_mobile = False
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(
    db: Session,
    db_user: models.User,
    user_in: Union[schemas.UserUpdate, schemas.BrokerAPICredentialsUpdate], # Accept either for flexibility
    original_email: Optional[str] = None,
    original_mobile_number: Optional[str] = None
) -> models.User:
    user_data = user_in.model_dump(exclude_unset=True)

    # Store new email/mobile if present, before applying all data
    new_email = user_data.get("email")
    new_mobile_number = user_data.get("mobile_number")

    # Apply standard field updates (excluding specific encrypted fields for now)
    for key, value in user_data.items():
        if key not in ['api_key', 'api_secret', 'access_token', 'refresh_token']: # Avoid direct set of these
            setattr(db_user, key, value)

    # If password needs to be updated, it should be handled by a separate function.

    # Encrypt broker API credentials if they are being updated
    from backend.core.security import encrypt_data
    if 'api_key' in user_data and user_data['api_key'] is not None:
        db_user.api_key_encrypted = encrypt_data(user_data.pop('api_key'))
    elif 'api_key' in user_data and user_data['api_key'] is None: # Explicitly nulling out
        db_user.api_key_encrypted = None

    if 'api_secret' in user_data and user_data['api_secret'] is not None:
        db_user.api_secret_encrypted = encrypt_data(user_data.pop('api_secret'))
    elif 'api_secret' in user_data and user_data['api_secret'] is None:
        db_user.api_secret_encrypted = None

    if 'access_token' in user_data and user_data['access_token'] is not None:
        db_user.access_token_encrypted = encrypt_data(user_data.pop('access_token'))
    elif 'access_token' in user_data and user_data['access_token'] is None:
        db_user.access_token_encrypted = None

    if 'refresh_token' in user_data and user_data['refresh_token'] is not None:
        db_user.refresh_token_encrypted = encrypt_data(user_data.pop('refresh_token'))
    elif 'refresh_token' in user_data and user_data['refresh_token'] is None:
        db_user.refresh_token_encrypted = None

    # Reset verification status if email/mobile changed
    if original_email is not None and new_email is not None and new_email != original_email:
        db_user.is_verified_email = False

    if original_mobile_number is not None and new_mobile_number is not None and new_mobile_number != original_mobile_number:
        db_user.is_verified_mobile = False
    # If new mobile is provided and original was None, also reset.
    elif original_mobile_number is None and new_mobile_number is not None:
        db_user.is_verified_mobile = False


    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: Union[str, int], password: str) -> Optional[models.User]:
    """
    Authenticates a user by email/mobile and password.
    Returns the user object if authentication is successful, otherwise None.
    """
    user = get_user_by_email_or_mobile(db, username)
    if not user:
        return None
    if not user.is_active: # Optional: check if user is active
        return None # Or raise an exception for inactive user
    if not verify_password(password, user.password_hash):
        return None
    return user


# OTP Management for User
def set_user_otp(db: Session, user: models.User, otp: str) -> models.User:
    """Sets OTP and its sent time for a user."""
    from datetime import datetime, timezone # Ensure timezone aware
    user.otp_secret = otp # Storing OTP directly for simplicity
    user.otp_sent_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def clear_user_otp(db: Session, user: models.User) -> models.User:
    """Clears OTP details for a user, typically after successful verification."""
    user.otp_secret = None
    user.otp_sent_at = None
    # Depending on use case, might also mark email/mobile as verified here
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user_email(db: Session, user: models.User) -> models.User:
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


# Subscription Plan CRUD (example, can be expanded)
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

# TODO: Add CRUD for other models as needed (BrokerAPICredentials, etc.)
