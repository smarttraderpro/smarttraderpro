# backend/tests/services/test_market_data_service.py
import pytest
from unittest.mock import patch, MagicMock
import yfinance as yf # To help with mocking yf.Ticker if needed for type hints

from backend.app.services.market_data_service import get_single_index_data, get_live_indices_data, TARGET_INDICES
from backend.app.schemas import IndexDataPoint

# Test get_single_index_data
@patch('backend.app.services.market_data_service.yf.Ticker')
def test_get_single_index_data_success(MockYfTicker):
    # Mock yf.Ticker(...).info behavior
    mock_ticker_instance = MockYfTicker.return_value
    mock_ticker_instance.info = {
        "regularMarketPrice": 18000.50,
        "previousClose": 17900.00,
        "symbol": "^NSEI" # yfinance might return the ticker symbol here
    }
    # Mock history as a fallback (though not strictly needed if info is complete)
    mock_ticker_instance.history.return_value = MagicMock(empty=True)


    data_point = get_single_index_data("^NSEI", "NIFTY 50")

    assert data_point is not None
    assert data_point.symbol == "NIFTY 50"
    assert data_point.ltp == 18000.50
    assert data_point.change == 100.50  # 18000.50 - 17900.00
    assert round(data_point.percent_change, 2) == round((100.50 / 17900.00) * 100, 2)
    MockYfTicker.assert_called_once_with("^NSEI")

@patch('backend.app.services.market_data_service.yf.Ticker')
def test_get_single_index_data_success_fallback_to_history(MockYfTicker):
    mock_ticker_instance = MockYfTicker.return_value
    # Simulate info missing ltp and prev_close initially
    mock_ticker_instance.info = {
        "symbol": "^NSEI",
        "regularMarketPrice": None, # Simulate missing LTP in info
        "previousClose": None      # Simulate missing prev close in info
    }
    # Prepare mock history data (using a simplified DataFrame-like structure for mocking)
    mock_hist_df = MagicMock()
    mock_hist_df.empty = False
    # Mocking iloc[-1] for LTP and iloc[-2] for prev_close
    # iloc[-1] is the most recent, iloc[-2] is the one before that.
    mock_hist_df.__getitem__.return_value.iloc.__getitem__.side_effect = lambda key: {
        -1: 18000.50, # LTP from history (last close)
        -2: 17900.00  # Previous close from history (second to last close)
    }[key]
    # Ensure 'Close' column exists and history has enough rows
    type(mock_hist_df.__getitem__.return_value).size = 2 # Make it seem like there are rows
    type(mock_hist_df.__getitem__.return_value).__len__ = lambda x: 2 # len() > 1

    mock_ticker_instance.history.return_value = mock_hist_df

    data_point = get_single_index_data("^NSEI", "NIFTY 50")

    assert data_point is not None
    assert data_point.symbol == "NIFTY 50"
    assert data_point.ltp == 18000.50
    assert data_point.change == 100.50
    assert round(data_point.percent_change, 2) == round((100.50 / 17900.00) * 100, 2)
    mock_ticker_instance.history.assert_called_once_with(period="2d")


@patch('backend.app.services.market_data_service.yf.Ticker')
def test_get_single_index_data_api_error(MockYfTicker):
    # Simulate yfinance call raising an exception
    MockYfTicker.side_effect = Exception("yfinance API error")
    data_point = get_single_index_data("^FAKETICKER", "FAKE INDEX")
    assert data_point is None

@patch('backend.app.services.market_data_service.yf.Ticker')
def test_get_single_index_data_missing_data_in_info_and_history(MockYfTicker):
    mock_ticker_instance = MockYfTicker.return_value
    mock_ticker_instance.info = {
        "regularMarketPrice": None, # Missing LTP
        "previousClose": None       # Missing previous close
    }
    # Simulate history also not providing data
    mock_hist_df_empty = MagicMock()
    mock_hist_df_empty.empty = True
    mock_ticker_instance.history.return_value = mock_hist_df_empty

    data_point = get_single_index_data("^NSEI", "NIFTY 50")
    assert data_point is None


# Test get_live_indices_data
@pytest.mark.asyncio
@patch('backend.app.services.market_data_service.get_single_index_data')
async def test_get_live_indices_data_all_success(MockGetSingleIndexData):
    # Mock get_single_index_data to return predictable IndexDataPoint objects
    def side_effect_func(ticker_symbol, display_name):
        if ticker_symbol == "^NSEI":
            return IndexDataPoint(symbol=display_name, ltp=18000, change=100, percentChange=0.56) # Use alias
        elif ticker_symbol == "^NSEBANK":
            return IndexDataPoint(symbol=display_name, ltp=40000, change=-200, percentChange=-0.50) # Use alias
        # Add other tickers from TARGET_INDICES as needed for complete test
        # For simplicity, assuming remaining TARGET_INDICES also use this generic success case
        return IndexDataPoint(symbol=display_name, ltp=1000, change=10, percentChange=1.0) # Use alias

    MockGetSingleIndexData.side_effect = side_effect_func

    live_data = await get_live_indices_data()

    assert len(live_data) == len(TARGET_INDICES)
    assert MockGetSingleIndexData.call_count == len(TARGET_INDICES)

    nifty_data = next((item for item in live_data if item.symbol == "NIFTY 50"), None)
    assert nifty_data is not None
    assert nifty_data.ltp == 18000

@pytest.mark.asyncio
@patch('backend.app.services.market_data_service.get_single_index_data')
async def test_get_live_indices_data_some_fail(MockGetSingleIndexData):
    # Simulate one ticker failing, others succeeding
    def side_effect_func(ticker_symbol, display_name):
        if ticker_symbol == "^NSEI":
            return IndexDataPoint(symbol=display_name, ltp=18000, change=100, percentChange=0.56) # Use alias
        elif ticker_symbol == "^NSEBANK":
            return None # Simulate failure for Nifty Bank
        # Add other tickers from TARGET_INDICES as needed for complete test
        # For simplicity, assuming remaining TARGET_INDICES also use this generic success case
        return IndexDataPoint(symbol=display_name, ltp=1000, change=10, percentChange=1.0) # Use alias

    MockGetSingleIndexData.side_effect = side_effect_func

    live_data = await get_live_indices_data()

    assert len(live_data) == len(TARGET_INDICES) - 1 # One less due to failure
    assert MockGetSingleIndexData.call_count == len(TARGET_INDICES)

    nifty_bank_data = next((item for item in live_data if item.symbol == "NIFTY BANK"), None)
    assert nifty_bank_data is None # Should not be in the list
    nifty_data = next((item for item in live_data if item.symbol == "NIFTY 50"), None)
    assert nifty_data is not None # Nifty 50 should still be there
    assert nifty_data.ltp == 18000
