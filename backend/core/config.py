# backend/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Trader Hub"
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "smarttrader"
    POSTGRES_PASSWORD: str = "password" # Replace with a strong password in production
    POSTGRES_DB: str = "smarttraderdb"
    DATABASE_URL: Optional[str] = None

    # JWT Settings
    SECRET_KEY: str = "a_very_secret_key_for_jwt_hs256" # REPLACE THIS IN PRODUCTION!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # 7 days

    # Encryption key for API credentials (Fernet needs a 32-byte URL-safe base64-encoded key)
    # Generate one using: from cryptography.fernet import Fernet; Fernet.generate_key().decode()
    CREDENTIALS_ENCRYPTION_KEY: str = "your_32_byte_url_safe_base64_encoded_key" # REPLACE THIS!

    # OTP Settings
    OTP_EXPIRY_MINUTES: int = 5
    # For a real app, you'd use an SMS gateway or email service
    # For now, we can simulate or log OTPs

    # CORS Origins (update for your frontend URL in production)
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"] # Add React and other frontend dev servers


    class Config:
        case_sensitive = True
        # env_file = ".env" # If you want to load from a .env file

settings = Settings()

# Construct DATABASE_URL if not set explicitly (e.g., for Docker)
if not settings.DATABASE_URL:
    settings.DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"

# It's good practice to validate that critical keys are set, especially CREDENTIALS_ENCRYPTION_KEY
if settings.CREDENTIALS_ENCRYPTION_KEY == "your_32_byte_url_safe_base64_encoded_key":
    print("WARNING: CREDENTIALS_ENCRYPTION_KEY is not set to a secure value in config.py. Please generate and set a proper key.")

if settings.SECRET_KEY == "a_very_secret_key_for_jwt_hs256":
    print("WARNING: SECRET_KEY is not set to a secure value in config.py. Please generate and set a proper key.")
