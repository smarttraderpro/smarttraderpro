# backend/app/api/v1/endpoints/market.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List # Not strictly needed if using schemas.LiveIndicesResponse directly

from backend.app import schemas
from backend.app.services.market_data_service import get_live_indices_data
# from backend.app.dependencies import get_current_active_user # If endpoint needs to be protected

router = APIRouter()

@router.get(
    "/live-indices",
    response_model=schemas.LiveIndicesResponse,
    summary="Get Live Market Data for Key Indices",
    description="Fetches and returns the latest market data (LTP, change, % change) for Nifty 50, Nifty Bank, Sensex, and India VIX using yfinance."
)
async def read_live_indices_data(
    # current_user: models.User = Depends(get_current_active_user) # Uncomment to protect endpoint
):
    """
    Endpoint to get live market data for predefined indices.
    Data is fetched on-demand using yfinance.
    """
    try:
        indices_data = await get_live_indices_data()
        if not indices_data:
            # This might happen if yfinance fails for all tickers, or if no tickers are defined (unlikely here)
            # Depending on desired behavior, could return 200 with empty list or an error.
            # For now, let's assume if some data is there, it's okay. If totally empty, it's an issue.
            # The service layer already prints errors for individual tickers.
            # If the list is empty, it means all failed.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not fetch live market data for any indices at this time. yfinance might be down or tickers are invalid."
            )

        # The service already returns a list of IndexDataPoint objects.
        # We wrap it in LiveIndicesResponse which also adds a timestamp.
        return schemas.LiveIndicesResponse(data=indices_data)

    except HTTPException as he: # Re-raise HTTPExceptions
        raise he
    except Exception as e:
        # Catch any other unexpected errors from the service or yfinance
        print(f"Unexpected error in /live-indices endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while fetching market data: {str(e)}"
        )

# Note: For a production system with frequent calls, implementing caching (e.g., with FastAPI Cache or Redis)
# for this endpoint would be highly recommended to avoid hitting yfinance too often and to improve response times.
# For example, cache results for 5-15 seconds.
