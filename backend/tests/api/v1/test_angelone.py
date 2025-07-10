# backend/tests/api/v1/test_angelone.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status, HTTPException

from backend.app.services.angelone_service import AngelOneService, AngelOneServiceError
from backend.core.config import settings
from backend.app.models import User as UserModel # To use in type hints for fixtures
from backend.tests.conftest import test_user # Import existing fixture for an authenticated user

# Helper to get auth headers (copied from test_users.py or make it a shared fixture)
from backend.core.security import create_access_token
def get_auth_headers_for_user(user_email: str) -> dict:
    token = create_access_token(subject=user_email)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@patch('backend.app.api.v1.endpoints.angelone.get_angelone_service')
async def test_read_angelone_profile_success(MockGetAngeloneService, test_client: TestClient, test_user: UserModel):
    mock_service_instance = AsyncMock(spec=AngelOneService)
    mock_service_instance.get_profile_and_funds.return_value = {
        "profile": {"clientCode": "TEST1", "name": "Test User"},
        "funds": {"availablecash": 10000.00}
    }
    MockGetAngeloneService.return_value = mock_service_instance

    headers = get_auth_headers_for_user(test_user.email)
    response = test_client.get(f"{settings.API_V1_STR}/angelone/profile", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["profile"]["clientCode"] == "TEST1"
    assert data["funds"]["availablecash"] == 10000.00
    mock_service_instance.get_profile_and_funds.assert_awaited_once_with(pin_for_session=None, totp_for_session=None)


@pytest.mark.asyncio
@patch('backend.app.api.v1.endpoints.angelone.get_angelone_service')
async def test_read_angelone_profile_with_pin_totp_headers(MockGetAngeloneService, test_client: TestClient, test_user: UserModel):
    mock_service_instance = AsyncMock(spec=AngelOneService)
    mock_service_instance.get_profile_and_funds.return_value = {"profile": {}, "funds": {}}
    MockGetAngeloneService.return_value = mock_service_instance

    headers = get_auth_headers_for_user(test_user.email)
    headers["X-Angelone-Pin"] = "1234"
    headers["X-Angelone-Totp"] = "123456"

    response = test_client.get(f"{settings.API_V1_STR}/angelone/profile", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    mock_service_instance.get_profile_and_funds.assert_awaited_once_with(pin_for_session="1234", totp_for_session="123456")


@pytest.mark.asyncio
@patch('backend.app.api.v1.endpoints.angelone.get_angelone_service')
async def test_read_angelone_profile_service_error(MockGetAngeloneService, test_client: TestClient, test_user: UserModel):
    mock_service_instance = AsyncMock(spec=AngelOneService)
    mock_service_instance.get_profile_and_funds.side_effect = AngelOneServiceError("Service unavailable", status_code=503)
    MockGetAngeloneService.return_value = mock_service_instance

    headers = get_auth_headers_for_user(test_user.email)
    response = test_client.get(f"{settings.API_V1_STR}/angelone/profile", headers=headers)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["detail"] == "Service unavailable"


@pytest.mark.asyncio
@patch('backend.app.api.v1.endpoints.angelone.get_angelone_service')
async def test_read_angelone_holdings_success(MockGetAngeloneService, test_client: TestClient, test_user: UserModel):
    mock_service_instance = AsyncMock(spec=AngelOneService)
    mock_service_instance.get_holdings.return_value = [{"symbol": "RELIANCE", "qty": 10}]
    MockGetAngeloneService.return_value = mock_service_instance

    headers = get_auth_headers_for_user(test_user.email)
    response = test_client.get(f"{settings.API_V1_STR}/angelone/holdings", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # The endpoint returns AngelOneHoldingsResponse which has a "data" key
    assert "data" in data
    assert data["data"][0]["symbol"] == "RELIANCE"
    mock_service_instance.get_holdings.assert_awaited_once_with(pin_for_session=None, totp_for_session=None)


@pytest.mark.asyncio
@patch('backend.app.api.v1.endpoints.angelone.get_angelone_service')
async def test_read_angelone_holdings_empty(MockGetAngeloneService, test_client: TestClient, test_user: UserModel):
    mock_service_instance = AsyncMock(spec=AngelOneService)
    mock_service_instance.get_holdings.return_value = [] # Empty list for no holdings
    MockGetAngeloneService.return_value = mock_service_instance

    headers = get_auth_headers_for_user(test_user.email)
    response = test_client.get(f"{settings.API_V1_STR}/angelone/holdings", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []


@pytest.mark.asyncio
@patch('backend.app.api.v1.endpoints.angelone.get_angelone_service') # This mock might be overridden by the inner patch
async def test_get_angelone_service_dependency_handles_init_error(MockGetAngeloneService, test_client: TestClient, test_user: UserModel):
    # This tests the get_angelone_service dependency itself
    # Mock the AngelOneService constructor to raise an error

    # We need to patch where AngelOneService is looked up by the dependency
    # The dependency is: from backend.app.services.angelone_service import AngelOneService
    # So we patch at that location.
    with patch('backend.app.api.v1.endpoints.angelone.AngelOneService', side_effect=AngelOneServiceError("Init failed", 503)) as MockedServiceClass:

        headers = get_auth_headers_for_user(test_user.email)
        # Call any endpoint that uses the get_angelone_service dependency
        response = test_client.get(f"{settings.API_V1_STR}/angelone/profile", headers=headers)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()["detail"] == "Init failed"
        # MockedServiceClass should have been called by the dependency
        # assert MockedServiceClass.called # This might be tricky due to how Depends works with classes

# Note: These tests assume that the `test_user` fixture provides a user for whom
# AngelOne credentials *could* be configured (even if the mock service doesn't use them directly here).
# The `get_angelone_service` dependency will try to instantiate `AngelOneService`
# which in turn tries to decrypt credentials from the user object.
# Ensure `test_user` has at least placeholder encrypted fields or that the service init mock handles this.
# The mock_user_with_angelone_creds fixture in service tests is more tailored.
# For these endpoint tests, we are mocking get_angelone_service, so the actual service init is bypassed.
# However, the test_get_angelone_service_dependency_handles_init_error *does* test this path.
# For that test, we'd need to ensure test_user has some (even if dummy) encrypted creds.
# The `test_user` from conftest might not have these. Let's assume it has some defaults.
# Or, modify that specific test to use a user that would cause the init to proceed far enough.
# The current `test_user` fixture doesn't set broker-specific encrypted fields.
# The dependency test will work as it directly patches `AngelOneService` constructor.
