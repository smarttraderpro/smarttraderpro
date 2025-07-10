# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Body # Added Body
from fastapi.security import OAuth2PasswordRequestForm # For form data login if preferred
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app import schemas, crud, models
from backend.db.session import get_db
from backend.core.security import create_access_token, create_refresh_token
from backend.core.config import settings

router = APIRouter()

# Changed response model as the structure is now a custom message dict
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate
):
    """
    Create a new user account.

    - **email**: User's email address (must be unique).
    - **password**: User's password (min 8 characters).
    - **mobile_number**: User's mobile number (optional, must be unique if provided).
    - **role**: User role (defaults to CLIENT).
    - **broker_preference**: Default broker preference (optional).

    Returns the created user's public information.
    """
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )
    if user_in.mobile_number:
        user_by_mobile = crud.get_user_by_mobile(db, mobile_number=user_in.mobile_number)
        if user_by_mobile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this mobile number already exists."
            )

    # Create the user (will be inactive by default as per updated crud.create_user)
    new_user = crud.create_user(db=db, user=user_in)

    # Generate OTP, store it, and send it to the user's email for verification
    try:
        otp = generate_otp()
        crud.set_user_otp(db, user=new_user, otp=otp)
        send_otp_email(email_to=new_user.email, otp=otp) # Simulated email sending
    except Exception as e:
        # If OTP sending fails, this is problematic.
        # For now, we might still return success for user creation but log the OTP error.
        # Or, we could roll back user creation, but that's more complex.
        # A robust system might queue OTP sending or have retries.
        print(f"Error sending OTP during signup for user {new_user.email}: {e}")
        # Potentially raise an HTTPException or return a specific error response part
        # For now, we'll let the user be created but OTP might not have "sent".
        # The user can request a new OTP later via /send-otp if needed.

    return {
        "message": "Signup successful. An OTP has been sent to your email for verification.",
        "user_id": new_user.id,
        "email": new_user.email,
        "is_active": new_user.is_active, # Will be False
        "is_verified_email": new_user.is_verified_email # Will be False
    }
    # Note: We are not returning the full UserPublic schema here anymore,
    # as the user is not yet fully "usable" in the same way.
    # Client should guide user to OTP verification.


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: schemas.LoginRequest = Body(...), # Explicitly mark as body, and required
    db: Session = Depends(get_db)
    # Option 2: Using FastAPI's OAuth2PasswordRequestForm for form data
    # form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Logs in a user and returns JWT access and refresh tokens.
    The `username` field in the request can be either the user's email address or mobile number.
    """
    user = crud.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/mobile or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires # Using email as subject for JWT
    )
    refresh_token = create_refresh_token(
        subject=user.email, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.post("/refresh-token", response_model=schemas.Token)
def refresh_access_token(
    current_user_email: str = Depends(lambda token: schemas.TokenData(email=token)), # Simplified dependency
    # In a real app, you'd have a proper dependency that validates the refresh token
    # For now, this is a placeholder and needs proper refresh token validation logic
    # For example: current_user: models.User = Depends(get_current_user_from_refresh_token)
    # where get_current_user_from_refresh_token would validate the refresh token
    # and return the user.
    # This current dependency is NOT secure for refresh tokens.
    # A proper implementation would expect the refresh token in the body or header,
    # validate it, and then issue a new access token.
    # Let's assume for now client sends its email and we just issue a token (INSECURE placeholder)
    db: Session = Depends(get_db) # db needed if we fetch user by email
):
    """
    Refresh access token.
    NOTE: This is a placeholder and needs a secure implementation for validating the refresh token.
    """
    user = crud.get_user_by_email(db, email=current_user_email.email) # type: ignore
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found, cannot refresh token",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        # Optionally, issue a new refresh token as well, or keep the old one
        # "refresh_token": create_refresh_token(subject=user.email)
    }

# TODO: Add endpoints for OTP send/verify later as per plan.
# TODO: Add endpoint for /users/me (get current user profile)
# TODO: Add proper dependency for get_current_user from access_token for protected routes.

from backend.core.otp import generate_otp, send_otp_email, send_otp_sms, is_otp_expired
from pydantic import EmailStr

@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp_to_user(
    otp_request: schemas.OTPRequest,
    db: Session = Depends(get_db)
):
    """
    Generate and send OTP to user's email or mobile.
    This can be used for account verification, password reset, 2FA, etc.
    """
    user = crud.get_user_by_email_or_mobile(db, identifier=otp_request.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email/mobile not found."
        )

    otp = generate_otp()
    updated_user_with_otp = crud.set_user_otp(db, user=user, otp=otp)

    # Use a more robust check for email vs mobile based on identifier content
    # And ensure the corresponding user field is populated.
    if "@" in str(otp_request.identifier):
        if not updated_user_with_otp.email:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User email not found for email identifier.")
        send_otp_email(email_to=updated_user_with_otp.email, otp=otp)
        return {"message": f"OTP sent to email {updated_user_with_otp.email}."}
    else: # Assumed to be mobile identifier
        if not updated_user_with_otp.mobile_number:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User mobile number not found for mobile identifier.")
        send_otp_sms(mobile_to=updated_user_with_otp.mobile_number, otp=otp)
        return {"message": f"OTP sent to mobile number {updated_user_with_otp.mobile_number}."}


@router.post("/verify-otp", status_code=status.HTTP_200_OK) # Or response_model=schemas.UserPublic if returning user
async def verify_user_otp(
    otp_verify_request: schemas.OTPVerify,
    db: Session = Depends(get_db)
):
    """
    Verify OTP provided by the user.
    If successful, could mark email/mobile as verified, or complete a 2FA login, etc.
    """
    user = crud.get_user_by_email_or_mobile(db, identifier=otp_verify_request.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email/mobile not found."
        )

    if not user.otp_secret or not user.otp_sent_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found for this user or never sent. Please request a new OTP."
        )

    if is_otp_expired(user.otp_sent_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )

    if user.otp_secret != otp_verify_request.otp:
        # TODO: Implement OTP attempt limits to prevent brute-force
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP."
        )

    # OTP is correct and not expired.
    message = "OTP verified successfully." # Default message

    identifier_str = str(otp_verify_request.identifier)
    action_taken = False

    if "@" in identifier_str and user.email == identifier_str:
        # This OTP is for email verification and account activation
        activated_user = crud.activate_user_and_verify_email(db, user=user)
        message = f"Email {activated_user.email} verified and account activated successfully."
        action_taken = True
    elif user.mobile_number == identifier_str: # Identifier was mobile
        # This OTP is for mobile verification (does not activate account by default in this flow)
        crud.verify_user_mobile(db, user=user)
        message = f"Mobile number {user.mobile_number} verified successfully."
        action_taken = True

    if not action_taken:
        # If OTP was valid but identifier didn't match a specific verification action known here
        # (e.g. future 2FA OTP), it's still a successful OTP verification for that context.
        # For now, this path means it wasn't for email or mobile verification as defined above.
        pass # message remains "OTP verified successfully."

    crud.clear_user_otp(db, user=user) # Clear OTP after successful verification regardless of specific action

    return {
        "message": message,
        "user_id": user.id,
        "is_active": user.is_active, # Reflects activation status
        "is_verified_email": user.is_verified_email,
        "is_verified_mobile": user.is_verified_mobile
    }
    # Optionally return user object: return schemas.UserPublic.from_orm(user)
