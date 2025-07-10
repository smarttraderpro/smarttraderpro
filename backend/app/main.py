# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.app.api.v1.api import api_router as api_v1_router
# from backend.db.session import engine # If using models.Base.metadata.create_all()
# from backend.app import models # If using models.Base.metadata.create_all()

# Create all tables in the database (alternative to Alembic for simple cases or initial dev)
# This should ideally be handled by Alembic migrations, especially for production.
# If you ran Alembic migrations, you don't need this.
# try:
#     models.Base.metadata.create_all(bind=engine)
#     print("Database tables created (if they didn't exist).")
# except Exception as e:
#     print(f"Error creating database tables: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        # allow_origins=["*"], # Allow all for development, be more restrictive in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

# Include the API router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# For development with uvicorn, you might run this file directly:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Add __init__.py files to directories to make them packages
# backend/app/api/__init__.py
# backend/app/api/v1/__init__.py
# backend/app/api/v1/endpoints/__init__.py
