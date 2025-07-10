# backend/tests/api/v1/test_users.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting
from typing import Dict

from backend.app import schemas, models # For role enum if needed
from backend.core.config import settings
from backend.core.security import create_access_token # To create tokens for auth

# Helper function to get authenticated headers
def get_auth_headers(user_email: str) -> Dict[str, str]:
    access_token = create_access_token(subject=user_email)
    return {"Authorization": f"Bearer {access_token}"}

# Test /users/me GET endpoint
def test_read_users_me_success(test_client: TestClient, test_user: models.User):
    headers = get_auth_headers(test_user.email)
    response = test_client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert response.status_code == 200
    user_profile = response.json()
    assert user_profile["email"] == test_user.email
    assert user_profile["id"] == test_user.id
    assert "password_hash" not in user_profile # Ensure sensitive data isn't returned

def test_read_users_me_unauthenticated(test_client: TestClient):
    response = test_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401 # FastAPI's default for missing auth with OAuth2PasswordBearer
    assert "not authenticated" in response.json()["detail"].lower()

def test_read_users_me_inactive_user(test_client: TestClient, test_user: models.User, db_session: Session):
    # Make user inactive
    test_user.is_active = False
    db_session.add(test_user)
    db_session.commit()

    headers = get_auth_headers(test_user.email)
    response = test_client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    # The get_current_active_user dependency should raise this
    assert response.status_code == 400
    assert "inactive user" in response.json()["detail"].lower()

    # Make user active again for other tests
    test_user.is_active = True
    db_session.add(test_user)
    db_session.commit()


# Test /users/me PUT endpoint
def test_update_users_me_success(test_client: TestClient, test_user: models.User, db_session: Session):
    headers = get_auth_headers(test_user.email)
    update_data = {
        "email": "updateduser@example.com",
        "mobile_number": "1112223333",
        "broker_preference": models.BrokerPreference.ZERODHA.value
    }
    response = test_client.put(f"{settings.API_V1_STR}/users/me", headers=headers, json=update_data)
    assert response.status_code == 200
    updated_profile = response.json()
    assert updated_profile["email"] == update_data["email"]
    assert updated_profile["mobile_number"] == update_data["mobile_number"]
    assert updated_profile["broker_preference"] == update_data["broker_preference"]

    # Verify email verification status changed
    assert updated_profile["is_verified_email"] is False # Email changed
    # Mobile verification status should also be false if mobile was updated
    # (assuming it was different from original or None)
    if test_user.mobile_number != update_data["mobile_number"]:
         assert updated_profile["is_verified_mobile"] is False

    db_session.refresh(test_user)
    assert test_user.email == update_data["email"]
    assert test_user.mobile_number == update_data["mobile_number"]
    assert test_user.broker_preference == models.BrokerPreference.ZERODHA
    assert test_user.is_verified_email is False

def test_update_users_me_email_conflict(test_client: TestClient, test_user: models.User, db_session: Session):
    # Create another user whose email we will try to take
    conflicting_user_data = {
        "email": "conflict@example.com",
        "password": "password123"
    }
    # Use client to create user to ensure it's in the same test DB session via override
    test_client.post(f"{settings.API_V1_STR}/auth/signup", json=conflicting_user_data)


    headers = get_auth_headers(test_user.email)
    update_data = {"email": "conflict@example.com"} # Try to take conflicting_user's email

    response = test_client.put(f"{settings.API_V1_STR}/users/me", headers=headers, json=update_data)
    assert response.status_code == 400
    assert "email address is already registered" in response.json()["detail"].lower()

def test_update_users_me_mobile_conflict(test_client: TestClient, test_user: models.User, db_session: Session):
    conflicting_mobile_user_data = {
        "email": "mobileconflict@example.com",
        "password": "password123",
        "mobile_number": "9998887777"
    }
    test_client.post(f"{settings.API_V1_STR}/auth/signup", json=conflicting_mobile_user_data)

    headers = get_auth_headers(test_user.email)
    update_data = {"mobile_number": "9998887777"}
    response = test_client.put(f"{settings.API_V1_STR}/users/me", headers=headers, json=update_data)
    assert response.status_code == 400
    assert "mobile number is already registered" in response.json()["detail"].lower()


# Test /users/me/broker-credentials PUT endpoint
def test_update_broker_credentials_success(test_client: TestClient, test_user: models.User, db_session: Session):
    headers = get_auth_headers(test_user.email)
    credentials_data = {
        "broker_user_id": "TESTCLIENT123",
        "api_key": "myapikey123",
        "api_secret": "myapisecret456",
        "access_token": "myaccesstoken789",
        "refresh_token": "myrefreshtokenabc"
    }
    response = test_client.put(f"{settings.API_V1_STR}/users/me/broker-credentials", headers=headers, json=credentials_data)
    assert response.status_code == 200

    db_session.refresh(test_user)
    assert test_user.broker_user_id == credentials_data["broker_user_id"]

    from backend.core.security import decrypt_data
    assert decrypt_data(test_user.api_key_encrypted) == credentials_data["api_key"]
    assert decrypt_data(test_user.api_secret_encrypted) == credentials_data["api_secret"]
    assert decrypt_data(test_user.access_token_encrypted) == credentials_data["access_token"]
    assert decrypt_data(test_user.refresh_token_encrypted) == credentials_data["refresh_token"]

def test_update_broker_credentials_partial(test_client: TestClient, test_user: models.User, db_session: Session):
    headers = get_auth_headers(test_user.email)
    credentials_data = {
        "api_key": "newapikey"
    }
    response = test_client.put(f"{settings.API_V1_STR}/users/me/broker-credentials", headers=headers, json=credentials_data)
    assert response.status_code == 200

    db_session.refresh(test_user)
    from backend.core.security import decrypt_data
    assert decrypt_data(test_user.api_key_encrypted) == credentials_data["api_key"]
    assert test_user.api_secret_encrypted is None # Assuming it was None before or not updated


# Test Admin endpoint for listing users (RBAC test)
def test_read_all_users_as_admin(test_client: TestClient, test_admin_user: models.User, test_user: models.User):
    headers = get_auth_headers(test_admin_user.email) # Authenticate as admin
    response = test_client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert response.status_code == 200
    users_list = response.json()
    assert len(users_list) >= 2 # test_admin_user and test_user at least
    emails = [u["email"] for u in users_list]
    assert test_admin_user.email in emails
    assert test_user.email in emails

def test_read_all_users_as_client(test_client: TestClient, test_user: models.User):
    headers = get_auth_headers(test_user.email) # Authenticate as client
    response = test_client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert response.status_code == 403 # Forbidden
    assert "user does not have the required role" in response.json()["detail"].lower()

def test_read_all_users_unauthenticated(test_client: TestClient):
    response = test_client.get(f"{settings.API_V1_STR}/users/")
    assert response.status_code == 401 # Not authenticated at all
    assert "not authenticated" in response.json()["detail"].lower()
