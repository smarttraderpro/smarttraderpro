# backend/tests/api/v1/test_market.py
import pytest
from unittest.mock import patch, AsyncMock # Added AsyncMock for async functions
from fastapi.testclient import TestClient
from fastapi import status

from backend.app.schemas import LiveIndicesResponse, IndexDataPoint # For constructing mock responses
from backend.core.config import settings
from datetime import datetime

# Test /market/live-indices endpoint
@patch('backend.app.api.v1.endpoints.market.get_live_indices_data', new_callable=AsyncMock)
def test_read_live_indices_data_success(MockGetLiveIndices, test_client: TestClient):
    # Prepare mock data that the service would return
    mock_data = [
        IndexDataPoint(symbol="NIFTY 50", ltp=18000.50, change=100.25, percentChange=0.56), # Use alias
        IndexDataPoint(symbol="NIFTY BANK", ltp=40000.75, change=-50.10, percentChange=-0.13), # Use alias
    ]
    MockGetLiveIndices.return_value = mock_data

    response = test_client.get(f"{settings.API_V1_STR}/market/live-indices")

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    assert "data" in response_json
    assert "timestamp" in response_json
    assert len(response_json["data"]) == 2

    assert response_json["data"][0]["symbol"] == "NIFTY 50"
    assert response_json["data"][0]["ltp"] == 18000.50
    assert response_json["data"][0]["change"] == 100.25
    assert response_json["data"][0]["percentChange"] == 0.56 # Check alias if by_alias=True in schema for response
                                                          # Default Pydantic v2 uses field name unless `by_alias=True` on dump.
                                                          # FastAPI usually respects alias for response_model.

    MockGetLiveIndices.assert_awaited_once()


@patch('backend.app.api.v1.endpoints.market.get_live_indices_data', new_callable=AsyncMock)
def test_read_live_indices_data_service_returns_empty(MockGetLiveIndices, test_client: TestClient):
    MockGetLiveIndices.return_value = [] # Simulate service returning no data (all tickers failed)

    response = test_client.get(f"{settings.API_V1_STR}/market/live-indices")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Could not fetch live market data" in response.json()["detail"]
    MockGetLiveIndices.assert_awaited_once()


@patch('backend.app.api.v1.endpoints.market.get_live_indices_data', new_callable=AsyncMock)
def test_read_live_indices_data_service_raises_exception(MockGetLiveIndices, test_client: TestClient):
    MockGetLiveIndices.side_effect = Exception("Simulated service layer error")

    response = test_client.get(f"{settings.API_V1_STR}/market/live-indices")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "An unexpected error occurred" in response.json()["detail"]
    assert "Simulated service layer error" in response.json()["detail"] # Ensure original error is part of detail
    MockGetLiveIndices.assert_awaited_once()

# Test response model structure rigorously
@patch('backend.app.api.v1.endpoints.market.get_live_indices_data', new_callable=AsyncMock)
def test_read_live_indices_data_response_schema(MockGetLiveIndices, test_client: TestClient):
    mock_data = [
        IndexDataPoint(symbol="SENSEX", ltp=60000.00, change=300.00, percentChange=0.50), # Use alias
    ]
    MockGetLiveIndices.return_value = mock_data

    response = test_client.get(f"{settings.API_V1_STR}/market/live-indices")
    assert response.status_code == status.HTTP_200_OK

    # Validate against the Pydantic schema
    # TestClient already does this if response_model is set correctly in endpoint,
    # but an explicit check can be useful.
    try:
        parsed_response = LiveIndicesResponse(**response.json())
        assert len(parsed_response.data) == 1
        assert parsed_response.data[0].symbol == "SENSEX"
        assert isinstance(parsed_response.timestamp, datetime)
    except Exception as e:
        pytest.fail(f"Response schema validation failed: {e}\nResponse JSON: {response.json()}")

    MockGetLiveIndices.assert_awaited_once()
