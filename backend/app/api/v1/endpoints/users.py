# backend/app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app import schemas, crud, models
from backend.app.dependencies import get_current_active_user, require_role # Added require_role
from backend.db.session import get_db

router = APIRouter()

@router.get("/me", response_model=schemas.UserPublic)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get current user's profile.
    """
    return current_user


@router.put("/me", response_model=schemas.UserPublic)
async def update_users_me(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserUpdate, # Schema for updating user profile
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update current user's profile.
    Fields like email, mobile_number, broker_preference can be updated.
    Password update should be handled by a separate endpoint for security (e.g., /change-password).
    """
    original_email = current_user.email
    original_mobile_number = current_user.mobile_number

    # Check if new email is already taken by another user
    if user_in.email and user_in.email != original_email:
        existing_user = crud.get_user_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email address is already registered to another account."
            )

    # Check if new mobile number is already taken by another user
    if user_in.mobile_number and user_in.mobile_number != original_mobile_number:
        existing_user = crud.get_user_by_mobile(db, mobile_number=user_in.mobile_number)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This mobile number is already registered to another account."
            )

    updated_user = crud.update_user(
        db=db,
        db_user=current_user,
        user_in=user_in,
        original_email=original_email,
        original_mobile_number=original_mobile_number
    )

    return updated_user


# Placeholder for admin to manage users (can be expanded later)
# @router.get("/", response_model=list[schemas.UserPublic])
# def read_users(
#     db: Session = Depends(get_db),
#     skip: int = 0,
#     limit: int = 100,
#     # current_admin_user: models.User = Depends(dependencies.get_current_admin_user) # Admin only
# ):
#     """
#     Retrieve users (admin only).
#     """
#     users = db.query(models.User).offset(skip).limit(limit).all()
#     return users


@router.put("/me/broker-credentials", response_model=schemas.UserPublic) # Or a more specific response
async def update_user_broker_credentials(
    *,
    db: Session = Depends(get_db),
    credentials_in: schemas.BrokerAPICredentialsUpdate,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update authenticated user's broker API credentials.
    The credentials will be encrypted before storing.
    """
    # We can pass credentials_in (which is a Pydantic model) directly to update_user.
    # The crud.update_user function is now responsible for checking field names
    # like 'api_key' and then encrypting them into 'api_key_encrypted'.

    # To ensure only broker credential fields are updated via this endpoint,
    # and not other UserUpdate fields, we pass 'credentials_in'.
    # The crud.update_user function will iterate through its fields.
    # Fields in BrokerAPICredentialsUpdate: broker_user_id, api_key, api_secret, access_token, refresh_token

    # If broker_user_id is part of credentials_in and not None, it will be set.
    # If api_key is part of credentials_in and not None, it will be encrypted and set to api_key_encrypted.
    # etc.

    updated_user = crud.update_user(db=db, db_user=current_user, user_in=credentials_in) # type: ignore
    # We use type: ignore because user_in expects UserUpdate, but BrokerAPICredentialsUpdate
    # is a compatible subset for the fields it handles.
    # A cleaner way might be to have a dedicated crud function or make update_user more generic
    # with field mapping. For now, this works because update_user iterates dict items.

    return updated_user


# Example Admin-only endpoint
@router.get("/", response_model=list[schemas.UserPublic])
async def read_all_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    # Use the new require_role dependency, correctly called
    current_admin_user: models.User = Depends(require_role(models.UserRole.ADMIN))
):
    """
    Retrieve all users. (Admin Only)
    """
    # The require_role(models.UserRole.ADMIN) dependency ensures only admin users can access this.
    # The result of the dependency (the admin user object) is available as current_admin_user.

    # Simple query to get users
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users
