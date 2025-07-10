# backend/tests/api/v1/test_auth_inactive_login.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.core.config import settings

def test_login_inactive_user(test_client: TestClient, db_session: Session):
    # 1. Sign up a new user (they will be inactive by default)
    signup_data = {
        "email": "inactiveuser@example.com",
        "password": "password123",
        "mobile_number": "9876500000" # Unique mobile
    }
    response_signup = test_client.post(f"{settings.API_V1_STR}/auth/signup", json=signup_data)
    assert response_signup.status_code == 201 # User created, inactive

    # 2. Attempt to login with this inactive user
    login_data = {"username": signup_data["email"], "password": signup_data["password"]}
    response_login = test_client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)

    assert response_login.status_code == 400 # As per current logic in /login for inactive users
    assert "inactive user" in response_login.json()["detail"].lower()

    # 3. (Optional but good) Verify OTP to make user active, then login should succeed
    from backend.app.crud import get_user_by_email
    db_user = get_user_by_email(db_session, email=signup_data["email"])
    assert db_user is not None
    assert db_user.is_active is False

    stored_otp = db_user.otp_secret
    assert stored_otp is not None

    verify_request_data = {"identifier": signup_data["email"], "otp": stored_otp}
    response_verify = test_client.post(f"{settings.API_V1_STR}/auth/verify-otp", json=verify_request_data)
    assert response_verify.status_code == 200
    assert response_verify.json()["is_active"] is True # Should be active now

    # 4. Attempt login again, should succeed now
    response_login_active = test_client.post(f"{settings.API_V1_STR}/auth/login", json=login_data)
    assert response_login_active.status_code == 200
    tokens = response_login_active.json()
    assert "access_token" in tokens
