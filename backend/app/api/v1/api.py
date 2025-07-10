# backend/app/api/v1/api.py
from fastapi import APIRouter

from backend.app.api.v1.endpoints import auth, users, market, angelone # Added angelone

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_router.include_router(angelone.router, prefix="/angelone", tags=["AngelOne Broker"])
