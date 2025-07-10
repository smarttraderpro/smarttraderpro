# backend/app/services/market_data_service.py
import yfinance as yf
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone # Added timezone

from backend.app.schemas import IndexDataPoint

# Define the target indices and their Yahoo Finance tickers
# Nifty 50: ^NSEI
# Nifty Bank: ^NSEBANK
# BSE Sensex: ^BSESN
# India VIX: ^INDIAVIX (Note: Ticker might vary, e.g. INDIAVIX.NS on some platforms. yfinance usually handles ^INDIAVIX)
TARGET_INDICES: Dict[str, str] = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "SENSEX": "^BSESN",
    "INDIA VIX": "^INDIAVIX"
}

def get_single_index_data(ticker_symbol: str, display_name: str) -> Optional[IndexDataPoint]:
    """
    Fetches live market data for a single index using yfinance.
    Returns an IndexDataPoint object or None if data fetching fails.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Using history for more reliable current data point access
        # '1d' period with '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo' intervals
        # For current price, '1d' with a fine interval or info can be used.
        # hist = ticker.history(period="1d", interval="1m") # Gets 1-minute data for today
        # if hist.empty:
        #     # Fallback or try ticker.info if hist is empty (e.g., pre-market)
        #     info = ticker.info
        #     ltp = info.get("regularMarketPrice") or info.get("currentPrice")
        #     prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        # else:
        #     ltp = hist['Close'].iloc[-1]
        #     # Previous close might need to be fetched from info or a '2d' history
        #     info = ticker.info # Often more reliable for previousClose
        #     prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

        # Simpler approach using ticker.info which is generally good for current data points
        # but can be delayed or less granular than history() for actively traded symbols.
        # For indices, .info is often sufficient for LTP and prev_close.
        info = ticker.info

        ltp = info.get("regularMarketPrice", info.get("currentPrice"))
        prev_close = info.get("previousClose", info.get("regularMarketPreviousClose"))

        if ltp is None or prev_close is None:
            print(f"Warning: Could not retrieve full LTP/previous_close for {display_name} ({ticker_symbol}). LTP: {ltp}, PrevClose: {prev_close}")
            # Attempt to get data from history as a fallback if info is incomplete
            hist_fallback = ticker.history(period="2d") # Get last two days to ensure we have previous close and current
            if not hist_fallback.empty:
                if ltp is None and len(hist_fallback['Close']) > 1: # Need at least 2 days for prev_close
                    ltp = hist_fallback['Close'].iloc[-1]
                if prev_close is None and len(hist_fallback['Close']) > 1:
                     prev_close = hist_fallback['Close'].iloc[-2] # Previous day's close

            if ltp is None or prev_close is None: # If still None after fallback
                 print(f"Error: Still unable to fetch complete data for {display_name} ({ticker_symbol}) after fallback.")
                 return None


        change = ltp - prev_close
        percent_change = (change / prev_close) * 100 if prev_close else 0.0

        return IndexDataPoint(
            symbol=display_name, # Use the display name like "NIFTY 50"
            ltp=round(float(ltp), 2),
            change=round(float(change), 2),
            percentChange=round(float(percent_change), 2) # Pydantic alias handles percentChange
        )

    except Exception as e:
        print(f"Error fetching data for {display_name} ({ticker_symbol}) from yfinance: {e}")
        # print(f"Ticker info for {ticker_symbol}: {ticker.info if 'ticker' in locals() else 'N/A'}")
        return None

async def get_live_indices_data() -> List[IndexDataPoint]:
    """
    Fetches live market data for all target indices.
    This function can be async to allow yfinance calls (which are blocking I/O)
    to be run in a thread pool by FastAPI.
    """
    indices_data: List[IndexDataPoint] = []
    for display_name, ticker_symbol in TARGET_INDICES.items():
        # In an async context, blocking calls like yfinance should be run in a thread pool
        # However, yfinance itself might not be inherently async-friendly without specific wrappers.
        # For simplicity in this step, direct calls are made. FastAPI handles this for sync functions in async routes.
        # If this becomes a performance bottleneck, consider libraries like `asycioyf` or running yf in `run_in_executor`.
        data_point = get_single_index_data(ticker_symbol, display_name)
        if data_point:
            indices_data.append(data_point)
    return indices_data

# Example usage (for testing this module directly):
if __name__ == "__main__":
    import asyncio

    async def main():
        print("Fetching live indices data...")
        data = await get_live_indices_data()
        if data:
            for item in data:
                print(item.model_dump_json(by_alias=True, indent=2))
        else:
            print("No data fetched.")

    # To run this test: python -m backend.app.services.market_data_service
    # Ensure yfinance is installed: pip install yfinance
    # Needs an active internet connection.
    asyncio.run(main())
