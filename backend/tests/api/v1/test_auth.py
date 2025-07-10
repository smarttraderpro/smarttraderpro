# backend/tests/api/v1/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if needed for db_session
from typing import Dict

from backend.app import schemas, models # For role enum if needed
from backend.core.config import settings

# Test User Signup
def test_signup_new_user(test_client: TestClient, db_session: Session):
    user_data = {
        "email": "newuser@example.com",
        "password": "new_password123",
        "mobile_number": "1234567890"
    }
    response = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=user_data)
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert created_user["mobile_number"] == user_data["mobile_number"]
    assert "id" in created_user
    assert created_user["is_active"] is True # Default from model or schema
    assert created_user["is_verified_email"] is False # Default from crud create_user
    assert created_user["is_verified_mobile"] is False # Default from crud create_user

    # Check user in DB (optional, but good for confirming)
    from backend.app.crud import get_user_by_email
    db_user = get_user_by_email(db_session, email=user_data["email"])
    assert db_user is not None
    assert db_user.email == user_data["email"]

def test_signup_existing_email(test_client: TestClient, test_user: models.User): # test_user fixture creates a user
    user_data = {
        "email": test_user.email, # Use email of existing test_user
        "password": "another_password123",
    }
    response = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=user_data)
    assert response.status_code == 400
    assert "email already exists" in response.json()["detail"].lower()

def test_signup_existing_mobile(test_client: TestClient, db_session: Session):
    # First, create a user with a specific mobile number
    initial_user_data = {
        "email": "mobiletestuser@example.com",
        "password": "password123",
        "mobile_number": "0987654321"
    }
    response_initial = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=initial_user_data)
    assert response_initial.status_code == 201

    # Attempt to sign up another user with the same mobile number
    new_user_data = {
        "email": "anothermobile@example.com",
        "password": "newpassword123",
        "mobile_number": "0987654321" # Same mobile number
    }
    response_duplicate = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=new_user_data)
    assert response_duplicate.status_code == 400
    assert "mobile number already exists" in response_duplicate.json()["detail"].lower()

def test_signup_invalid_email(test_client: TestClient):
    user_data = {"email": "not-an-email", "password": "password123"}
    response = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=user_data)
    assert response.status_code == 422 # Pydantic validation error

def test_signup_short_password(test_client: TestClient):
    user_data = {"email": "shortpass@example.com", "password": "short"}
    response = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=user_data)
    assert response.status_code == 422 # Pydantic validation error (constr min_length)


# Test User Login
def test_login_success(test_client: TestClient, test_user: models.User):
    login_data = {"username": test_user.email, "password": "testpassword"}
    response = test_client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_login_success_with_mobile(test_client: TestClient, db_session: Session):
    # Create a user with a mobile number for this test
    signup_data = {
        "email": "loginmobile@example.com",
        "password": "mobilepassword",
        "mobile_number": "1122334455"
    }
    test_client.post(f"{settings.API_V1_STR}/auth/signup", json=signup_data) # Create the user

    login_data = {"username": "1122334455", "password": "mobilepassword"} # Login with mobile
    response = test_client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens

def test_login_incorrect_password(test_client: TestClient, test_user: models.User):
    login_data = {"username": test_user.email, "password": "wrongpassword"}
    response = test_client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)
    assert response.status_code == 401
    assert "incorrect email/mobile or password" in response.json()["detail"].lower()

def test_login_user_not_found(test_client: TestClient):
    login_data = {"username": "nonexistent@example.com", "password": "password"}
    response = test_client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)
    assert response.status_code == 401 # Or 404 depending on how you want to reveal info
    assert "incorrect email/mobile or password" in response.json()["detail"].lower()


# Test Token Refresh (Basic placeholder, as refresh logic is not fully secure yet)
# This test will need significant rework when proper refresh token validation is in place.
# For now, it tests the placeholder logic.
@pytest.mark.skip(reason="Refresh token endpoint is a placeholder and not secure/fully functional yet")
def test_refresh_token(test_client: TestClient, test_user: models.User):
    # This assumes the placeholder /refresh-token endpoint which might just take an email
    # A real test would involve getting a refresh token from login, then using it.

    # First, login to get a refresh token (if the endpoint provided one)
    login_data = {"username": test_user.email, "password": "testpassword"}
    login_response = test_client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)
    assert login_response.status_code == 200
    # refresh_token = login_response.json().get("refresh_token")
    # assert refresh_token is not None

    # The current placeholder refresh endpoint uses a dummy dependency.
    # We'll simulate a request as if we had a valid (but unverified) refresh token context.
    # This part is highly dependent on how the actual refresh mechanism is implemented.
    # The current auth.py refresh endpoint takes current_user_email from a dummy dependency.
    # This is not how it would work with a real refresh token.

    # If the refresh endpoint expected a refresh token in Authorization header:
    # headers = {"Authorization": f"Bearer {refresh_token}"}
    # response = test_client.post(f"{settings.API_V1_STR}/auth/refresh-token", headers=headers)

    # Given the current placeholder in auth.py for /refresh-token,
    # which uses a simplified `Depends(lambda token: schemas.TokenData(email=token))`
    # and expects a token that is just the email string for the purpose of this placeholder.
    # This is NOT how a real refresh token works.
    # The dependency `Depends(lambda token: schemas.TokenData(email=token))` is not standard.
    # It implies the "token" passed is just the email.
    # Let's assume we need to pass the email in a specific way that the placeholder expects.
    # The current code is: current_user_email: str = Depends(lambda token: schemas.TokenData(email=token))
    # This is very unusual. FastAPI's Depends usually works with request parts (headers, body, query).
    # This lambda seems to expect 'token' to be directly the email.
    # This will likely fail or needs a very specific (and incorrect) way of calling.
    # Let's assume it's trying to get a "token" from the Authorization header and that token is the email.

    # This test needs to be rewritten once the refresh token logic is correctly implemented.
    # For now, skipping it as it's not testable in a meaningful way with the current placeholder.
    pass


# Test OTP Functionality
def test_send_otp_to_email(test_client: TestClient, test_user: models.User, db_session: Session, capsys):
    otp_request_data = {"identifier": test_user.email}
    response = test_client.post(f"{settings.API_V1_STR}/auth/send-otp", json=otp_request_data)
    assert response.status_code == 200
    assert f"OTP sent to email {test_user.email}" in response.json()["message"]

    # Check console output for simulated email
    captured = capsys.readouterr()
    assert f"Simulating sending OTP to email: {test_user.email}" in captured.out

    # Check if OTP is stored in DB (temporarily)
    db_session.refresh(test_user) # Refresh user from db_session used by test_client
    assert test_user.otp_secret is not None
    assert len(test_user.otp_secret) == 6 # Default OTP length
    assert test_user.otp_sent_at is not None

def test_send_otp_to_mobile(test_client: TestClient, db_session: Session, capsys):
    # Create a user with a mobile number for this test
    user_data = {
        "email": "otpmobile@example.com",
        "password": "otppassword",
        "mobile_number": "5551234567"
    }
    signup_response = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=user_data)
    assert signup_response.status_code == 201
    signed_up_user_email = signup_response.json()["email"]

    otp_request_data = {"identifier": user_data["mobile_number"]}
    response = test_client.post(f"{settings.API_V1_STR}/auth/send-otp", json=otp_request_data)
    assert response.status_code == 200
    assert f"OTP sent to mobile number {user_data['mobile_number']}" in response.json()["message"]

    captured = capsys.readouterr() # Capture print output from send_otp_sms
    assert f"Simulating sending OTP to mobile: {user_data['mobile_number']}" in captured.out

    from backend.app.crud import get_user_by_email
    db_user = get_user_by_email(db_session, email=signed_up_user_email)
    assert db_user is not None
    assert db_user.otp_secret is not None
    assert len(db_user.otp_secret) == 6
    assert db_user.otp_sent_at is not None


def test_send_otp_user_not_found(test_client: TestClient):
    otp_request_data = {"identifier": "nonexistentuser@example.com"}
    response = test_client.post(f"{settings.API_V1_STR}/auth/send-otp", json=otp_request_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_verify_otp_email_success(test_client: TestClient, test_user: models.User, db_session: Session):
    # 1. Send OTP
    otp_request_data = {"identifier": test_user.email}
    test_client.post(f"{settings.API_V1_STR}/auth/send-otp", json=otp_request_data)

    db_session.refresh(test_user)
    stored_otp = test_user.otp_secret
    assert stored_otp is not None

    # 2. Verify OTP
    verify_request_data = {"identifier": test_user.email, "otp": stored_otp}
    response = test_client.post(f"{settings.API_V1_STR}/auth/verify-otp", json=verify_request_data)
    assert response.status_code == 200
    assert f"Email {test_user.email} verified successfully" in response.json()["message"]

    db_session.refresh(test_user)
    assert test_user.is_verified_email is True
    assert test_user.otp_secret is None # OTP should be cleared after verification

def test_verify_otp_mobile_success(test_client: TestClient, db_session: Session):
    # 1. Create user and send OTP to mobile
    user_data = {
        "email": "verifyotp@example.com",
        "password": "verifyotppass",
        "mobile_number": "7778889999"
    }
    signup_res = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=user_data)
    user_id = signup_res.json()["id"]

    otp_request_data = {"identifier": user_data["mobile_number"]}
    test_client.post(f"{settings.API_V1_STR}/auth/send-otp", json=otp_request_data)

    from backend.app.crud import get_user
    db_user = get_user(db_session, user_id=user_id)
    assert db_user is not None
    stored_otp = db_user.otp_secret
    assert stored_otp is not None

    # 2. Verify OTP
    verify_request_data = {"identifier": user_data["mobile_number"], "otp": stored_otp}
    response = test_client.post(f"{settings.API_V1_STR}/auth/verify-otp", json=verify_request_data)
    assert response.status_code == 200
    assert f"Mobile number {user_data['mobile_number']} verified successfully" in response.json()["message"]

    db_session.refresh(db_user)
    assert db_user.is_verified_mobile is True
    assert db_user.otp_secret is None


def test_verify_otp_invalid(test_client: TestClient, test_user: models.User, db_session: Session):
    otp_request_data = {"identifier": test_user.email}
    send_response = test_client.post(f"{settings.API_V1_STR}/auth/send-otp", json=otp_request_data)
    assert send_response.status_code == 200 # Ensure OTP was sent successfully

    verify_request_data = {"identifier": test_user.email, "otp": "wrong123"} # 8 chars, valid format but incorrect value
    response = test_client.post(f"{settings.API_V1_STR}/auth/verify-otp", json=verify_request_data)
    assert response.status_code == 400
    assert "invalid otp" in response.json()["detail"].lower()

def test_verify_otp_expired(test_client: TestClient, test_user: models.User, db_session: Session):
    from datetime import datetime, timedelta, timezone
    from backend.core.config import settings as app_settings

    # 1. Send OTP
    otp_request_data = {"identifier": test_user.email}
    test_client.post(f"{settings.API_V1_STR}/auth/send-otp", json=otp_request_data)

    db_session.refresh(test_user)
    stored_otp = test_user.otp_secret
    assert stored_otp is not None

    # 2. Manually expire the OTP in the database
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=app_settings.OTP_EXPIRY_MINUTES + 5)
    test_user.otp_sent_at = expired_time
    db_session.add(test_user)
    db_session.commit()

    # 3. Attempt to Verify OTP
    verify_request_data = {"identifier": test_user.email, "otp": stored_otp}
    response = test_client.post(f"{settings.API_V1_STR}/auth/verify-otp", json=verify_request_data)
    assert response.status_code == 400
    assert "otp has expired" in response.json()["detail"].lower()

def test_verify_otp_not_sent(test_client: TestClient, test_user: models.User):
    # Ensure no OTP is set for test_user initially, or clear it
    test_user.otp_secret = None
    test_user.otp_sent_at = None
    # db_session.commit() # Already handled by fixture teardown if changes were made

    verify_request_data = {"identifier": test_user.email, "otp": "anyotp"}
    response = test_client.post(f"{settings.API_V1_STR}/auth/verify-otp", json=verify_request_data)
    assert response.status_code == 400
    assert "otp not found" in response.json()["detail"].lower()

# Note: Pytest's `capsys` fixture is used to capture stdout/stderr for simulated OTP sending.
# Need to create __init__.py in backend/tests/api and backend/tests/api/v1
# for pytest to discover tests correctly.
