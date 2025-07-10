# backend/app/api/v1/endpoints/angelone.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional, Any, Dict, List

from backend.app import models, schemas # For User model and response schemas
from backend.app.dependencies import get_current_active_user
from backend.app.services.angelone_service import AngelOneService, AngelOneServiceError
from backend.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# Helper to instantiate service, could be a dependency too
def get_angelone_service(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)) -> AngelOneService:
    try:
        return AngelOneService(db=db, user=current_user)
    except AngelOneServiceError as e:
        # This handles cases like SDK not found or user credentials not configured
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/profile",
    response_model=schemas.AngelOneProfileResponse, # Use the defined schema
    summary="Get AngelOne User Profile and Funds",
    description="Fetches the logged-in user's profile and fund details from their AngelOne account."
)
async def read_angelone_profile(
    service: AngelOneService = Depends(get_angelone_service),
    x_angelone_pin: Optional[str] = Header(None, description="User's AngelOne PIN/Password (if new session needed)"),
    x_angelone_totp: Optional[str] = Header(None, description="User's current AngelOne TOTP (if new session needed)")
) -> schemas.AngelOneProfileResponse: # Return type hint matches response_model
    try:
        # The service.get_profile_and_funds() should return a dictionary
        # that can be parsed into AngelOneProfile and AngelOneUserFunds.
        # For simplicity, let's assume it returns a dict with 'profile' and 'funds' keys.
        # This might need adjustment based on actual service return structure.
        data = await service.get_profile_and_funds(
            pin_for_session=x_angelone_pin,
            totp_for_session=x_angelone_totp
        )
        if data is None or "profile" not in data or "funds" not in data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile or funds data not found or unable to fetch.")

        # Construct the response model. This assumes `data` is a dict like:
        # {"profile": {...}, "funds": {...}}
        # If service.get_profile_and_funds directly returns a dict that matches AngelOneProfileResponse,
        # then FastAPI can often construct it automatically if the dict keys match.
        # For clarity, explicit construction:
        return schemas.AngelOneProfileResponse(
            profile=schemas.AngelOneProfile(**data["profile"]),
            funds=schemas.AngelOneUserFunds(**data["funds"])
        )
    except AngelOneServiceError as e:
        # If e.status_code is 401 and message contains "session requires password/PIN and TOTP",
        # frontend should know to prompt for these.
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        print(f"Unexpected error in /angelone/profile endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/holdings",
    response_model=schemas.AngelOneHoldingsResponse, # Use the defined schema
    summary="Get AngelOne User Holdings",
    description="Fetches the logged-in user's current stock holdings from their AngelOne account."
)
async def read_angelone_holdings(
    service: AngelOneService = Depends(get_angelone_service),
    x_angelone_pin: Optional[str] = Header(None, description="User's AngelOne PIN/Password (if new session needed)"),
    x_angelone_totp: Optional[str] = Header(None, description="User's current AngelOne TOTP (if new session needed)")
) -> schemas.AngelOneHoldingsResponse: # Return type hint matches response_model
    try:
        holdings_list = await service.get_holdings(
            pin_for_session=x_angelone_pin,
            totp_for_session=x_angelone_totp
        )
        # The service.get_holdings() is expected to return a list of dicts,
        # each matching AngelOneHolding schema.
        # If holdings_list is None (service indicated total failure) or empty list (valid, no holdings)

        # If service returns None for total failure (already handled by exception in service usually)
        if holdings_list is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holdings data not found or unable to fetch.")

        # The AngelOneHoldingsResponse schema expects a 'data' key with the list.
        return schemas.AngelOneHoldingsResponse(data=holdings_list)
    except AngelOneServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        print(f"Unexpected error in /angelone/holdings endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Note: The use of Headers for PIN and TOTP is one way to pass them per-request if needed.
# The frontend would need to collect these from the user if a 401 error from these endpoints
# indicates they are required for a new AngelOne session.
# A more complex flow might involve a dedicated /angelone/initiate-session endpoint.
# For now, these headers provide a mechanism if the service._ensure_session() requires them.
