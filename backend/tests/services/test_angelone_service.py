# backend/tests/services/test_angelone_service.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session # For db_session type hint

from backend.app.services.angelone_service import AngelOneService, AngelOneServiceError
from backend.app.models import User
from backend.app import schemas # For potential schema usage if needed
from backend.core.security import encrypt_data # For setting up mock user credentials

# Fixture for a mock user with AngelOne credentials
@pytest.fixture
def mock_user_with_angelone_creds(db_session: Session) -> User:
    # Using a real user object but with mocked encrypted data for this test
    # In a full integration test, this user would come from test_user fixture
    # and credentials would be set via an API call.
    # Here, we construct it directly for service layer testing.
    user = User(
        id=1,
        email="angeluser@example.com",
        password_hash="dummy_password_hash", # Added
        broker_user_id="ANGELCLIENT123", # Angel Client ID
        api_key_encrypted=encrypt_data("angelapikey"),
        api_secret_encrypted=encrypt_data("angelapisecret"),
        access_token_encrypted=None, # No initial AngelOne session token
        refresh_token_encrypted=None,
        is_active=True,
        role=models.UserRole.CLIENT # Added default role
    )
    # db_session.add(user) # Not adding to DB for this unit test, service takes User object
    # db_session.commit()
    return user

@pytest.fixture
def mock_user_with_existing_session(db_session: Session) -> User:
    user = User(
        id=2,
        email="angelsession@example.com",
        password_hash="dummy_session_password_hash", # Added
        broker_user_id="ANGELSESSION456",
        api_key_encrypted=encrypt_data("key123"),
        api_secret_encrypted=encrypt_data("secret456"),
        access_token_encrypted=encrypt_data("valid_angel_session_token"),
        is_active=True,
        role=models.UserRole.CLIENT # Added default role
    )
    return user


# Mock the SmartConnect class from the SDK
@patch('backend.app.services.angelone_service.SmartConnect')
def test_angelone_service_init_success(MockSmartConnect, mock_user_with_angelone_creds: User, db_session: Session):
    mock_sdk_instance = MockSmartConnect.return_value
    service = AngelOneService(db=db_session, user=mock_user_with_angelone_creds)

    MockSmartConnect.assert_called_once_with(api_key="angelapikey")
    assert service.smart_connect is mock_sdk_instance
    assert service.api_key == "angelapikey"
    assert service.client_id == "ANGELCLIENT123"
    assert service.session_token is None # No existing token initially

@patch('backend.app.services.angelone_service.SmartConnect')
def test_angelone_service_init_with_existing_session(MockSmartConnect, mock_user_with_existing_session: User, db_session: Session):
    mock_sdk_instance = MockSmartConnect.return_value
    service = AngelOneService(db=db_session, user=mock_user_with_existing_session)

    MockSmartConnect.assert_called_once_with(api_key="key123")
    assert service.session_token == "valid_angel_session_token"
    mock_sdk_instance.setAccessToken.assert_called_once_with("valid_angel_session_token")


@patch('backend.app.services.angelone_service.SmartConnect')
def test_angelone_service_init_missing_creds(MockSmartConnect, db_session: Session):
    user_no_creds = User(id=3, email="nocreds@example.com", is_active=True) # Missing API key and client ID
    with pytest.raises(AngelOneServiceError) as excinfo:
        AngelOneService(db=db_session, user=user_no_creds)
    assert "API key or Client ID not configured" in str(excinfo.value)
    assert excinfo.value.status_code == 400

# Test _ensure_session method
@pytest.mark.asyncio
@patch('backend.app.services.angelone_service.SmartConnect')
async def test_ensure_session_uses_existing_valid_token(MockSmartConnect, mock_user_with_existing_session: User, db_session: Session):
    mock_sdk_instance = MockSmartConnect.return_value
    # Simulate getProfile succeeding, indicating token is valid
    mock_sdk_instance.getProfile.return_value = {"status": True, "data": {"clientCode": "test"}}

    service = AngelOneService(db=db_session, user=mock_user_with_existing_session) # Initializes with token

    result = await service._ensure_session("pin", "totp") # PIN/TOTP provided but shouldn't be used

    assert result is True
    assert service.session_token == "valid_angel_session_token" # Token remains the same
    mock_sdk_instance.getProfile.assert_called_once() # Check that validity was tested
    mock_sdk_instance.generateSession.assert_not_called() # New session should not be generated

@pytest.mark.asyncio
@patch('backend.app.services.angelone_service.SmartConnect')
async def test_ensure_session_generates_new_token_if_none_exists(MockSmartConnect, mock_user_with_angelone_creds: User, db_session: Session):
    mock_sdk_instance = MockSmartConnect.return_value
    # Simulate generateSession succeeding
    mock_sdk_instance.generateSession.return_value = {
        "status": True,
        "message": "SUCCESS",
        "errorcode": "",
        "data": {
            "jwtToken": "new_jwt_token",
            "refreshToken": "new_refresh_token",
            "feedToken": "new_feed_token"
        }
    }
    # Simulate getProfile failing initially if called by constructor to set existing token
    # (though mock_user_with_angelone_creds has no initial token, so this won't be called by constructor path)
    # For _ensure_session, if token is None, it goes straight to generateSession if PIN/TOTP provided.

    service = AngelOneService(db=db_session, user=mock_user_with_angelone_creds) # No initial token

    result = await service._ensure_session(user_pin_or_password="userpin", totp="123456")

    assert result is True
    assert service.session_token == "new_jwt_token"
    mock_sdk_instance.generateSession.assert_called_once_with("ANGELCLIENT123", "userpin", "123456")
    # Check if user model in DB would be updated (requires db_session to be a real session that can commit)
    # For now, assume db_session.commit is called in service.
    # We can also check the user object passed to the service if it's mutated.
    assert mock_user_with_angelone_creds.access_token_encrypted is not None
    assert mock_user_with_angelone_creds.refresh_token_encrypted is not None


@pytest.mark.asyncio
@patch('backend.app.services.angelone_service.SmartConnect')
async def test_ensure_session_regenerates_if_token_invalid(MockSmartConnect, mock_user_with_existing_session: User, db_session: Session):
    mock_sdk_instance = MockSmartConnect.return_value
    # Simulate getProfile (token validity check) failing, then generateSession succeeding
    mock_sdk_instance.getProfile.side_effect = AngelOneServiceError("Token invalid", 401) # Or SDK specific exception
    mock_sdk_instance.generateSession.return_value = {
        "status": True, "data": {"jwtToken": "fresh_token", "refreshToken": "fresh_refresh"}
    }

    service = AngelOneService(db=db_session, user=mock_user_with_existing_session)

    result = await service._ensure_session(user_pin_or_password="userpin", totp="123456")

    assert result is True
    assert service.session_token == "fresh_token"
    mock_sdk_instance.getProfile.assert_called_once() # Attempted to validate old token
    mock_sdk_instance.generateSession.assert_called_once_with(mock_user_with_existing_session.broker_user_id, "userpin", "123456")


@pytest.mark.asyncio
@patch('backend.app.services.angelone_service.SmartConnect')
async def test_ensure_session_fails_if_pin_totp_needed_but_not_provided(MockSmartConnect, mock_user_with_angelone_creds: User, db_session: Session):
    # User has no initial session token
    service = AngelOneService(db=db_session, user=mock_user_with_angelone_creds)

    with pytest.raises(AngelOneServiceError) as excinfo:
        await service._ensure_session() # Call without PIN/TOTP
    assert "session requires password/PIN and TOTP" in str(excinfo.value)
    assert excinfo.value.status_code == 401


# Test get_profile_and_funds
@pytest.mark.asyncio
@patch.object(AngelOneService, '_ensure_session', new_callable=AsyncMock) # Patching the method on the class
async def test_get_profile_and_funds_success(MockEnsureSession, mock_user_with_angelone_creds: User, db_session: Session):
    MockEnsureSession.return_value = True # Simulate session is ensured

    service = AngelOneService(db=db_session, user=mock_user_with_angelone_creds)
    # Mock the actual SDK call made after session is ensured
    service.smart_connect.getProfile = MagicMock(return_value={"status": True, "data": {"clientName": "Test User", "availableCash": "10000"}})

    profile_data = await service.get_profile_and_funds("pin", "totp") # PIN/TOTP passed but _ensure_session is mocked

    assert profile_data is not None
    assert profile_data["clientName"] == "Test User"
    MockEnsureSession.assert_awaited_once_with("pin", "totp")
    service.smart_connect.getProfile.assert_called_once()


# Test get_holdings
@pytest.mark.asyncio
@patch.object(AngelOneService, '_ensure_session', new_callable=AsyncMock)
async def test_get_holdings_success(MockEnsureSession, mock_user_with_angelone_creds: User, db_session: Session):
    MockEnsureSession.return_value = True

    service = AngelOneService(db=db_session, user=mock_user_with_angelone_creds)
    mock_holdings = [{"tradingsymbol": "SBIN-EQ", "quantity": 10}]
    service.smart_connect.getHolding = MagicMock(return_value={"status": True, "data": mock_holdings})

    holdings_data = await service.get_holdings("pin", "totp")

    assert holdings_data is not None
    assert len(holdings_data) == 1
    assert holdings_data[0]["tradingsymbol"] == "SBIN-EQ"
    MockEnsureSession.assert_awaited_once_with("pin", "totp")
    service.smart_connect.getHolding.assert_called_once()

@pytest.mark.asyncio
@patch.object(AngelOneService, '_ensure_session', new_callable=AsyncMock)
async def test_get_holdings_api_returns_error_status(MockEnsureSession, mock_user_with_angelone_creds: User, db_session: Session):
    MockEnsureSession.return_value = True

    service = AngelOneService(db=db_session, user=mock_user_with_angelone_creds)
    service.smart_connect.getHolding = MagicMock(return_value={"status": False, "message": "Failed to fetch", "errorcode": "AB1234"})

    with pytest.raises(AngelOneServiceError) as excinfo:
        await service.get_holdings("pin", "totp")
    assert "Failed to fetch" in str(excinfo.value)
    assert excinfo.value.status_code == 502 # Bad Gateway for API error


@pytest.mark.asyncio
@patch.object(AngelOneService, '_ensure_session', new_callable=AsyncMock)
async def test_get_holdings_session_expired_error(MockEnsureSession, mock_user_with_angelone_creds: User, db_session: Session):
    MockEnsureSession.return_value = True # Session was initially fine

    service = AngelOneService(db=db_session, user=mock_user_with_angelone_creds)
    # Simulate API call returns session expired error
    service.smart_connect.getHolding = MagicMock(return_value={"status": False, "message": "Session Expired", "errorcode": "AG8001"})

    with pytest.raises(AngelOneServiceError) as excinfo:
        await service.get_holdings("pin", "totp")
    assert "AngelOne session expired" in str(excinfo.value)
    assert excinfo.value.status_code == 401
    # Check if token was cleared from user object (in a real DB session, this would be persisted)
    # This depends on how the mock_user object is managed across tests if it's from a fixture.
    # For this test, the service modifies the user object it was initialized with.
    assert mock_user_with_angelone_creds.access_token_encrypted is None
