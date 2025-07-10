# backend/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import settings

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# JWT Token Handling
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, expected_type: Optional[str] = "access") -> Optional[str]:
    """
    Verifies a JWT token and returns the subject (e.g., user ID or email) if valid.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        token_sub: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        token_exp: Optional[int] = payload.get("exp")

        if token_sub is None or token_type is None or token_exp is None:
            return None # Invalid token structure

        if datetime.fromtimestamp(token_exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return None # Token expired

        if expected_type and token_type != expected_type:
            return None # Incorrect token type (e.g. refresh token used as access token)

        return token_sub
    except JWTError:
        return None


# TODO: Implement Fernet encryption for API keys if not already part of a broader service
# For now, placeholder if we decide to put encryption utils here.
# from cryptography.fernet import Fernet
# CREDENTIALS_ENCRYPTION_KEY = settings.CREDENTIALS_ENCRYPTION_KEY
# if CREDENTIALS_ENCRYPTION_KEY == "your_32_byte_url_safe_base64_encoded_key":
#     print("WARNING: Using default CREDENTIALS_ENCRYPTION_KEY. THIS IS INSECURE. Generate a new key.")
#     # In a real app, you might raise an error or use a securely generated default only for local dev.
#     # For now, we'll allow it to proceed for sandbox, but this needs to be addressed.
#     # fernet = Fernet(Fernet.generate_key()) # Fallback, but key won't be persistent
#     fernet = Fernet(b'Zg30p5FL9xM623j3lTHY_9x9X7jP8o6wCw2q0i9uYl8=') # Example fixed key for dev
# else:
#     fernet = Fernet(CREDENTIALS_ENCRYPTION_KEY.encode())


# def encrypt_data(data: str) -> str:
#     if not data:
#         return ""
#     return fernet.encrypt(data.encode()).decode()

# def decrypt_data(encrypted_data: str) -> str:
#     if not encrypted_data:
#         return ""
#     return fernet.decrypt(encrypted_data.encode()).decode()

# The encryption part will be more fleshed out when handling broker API keys specifically.
# For now, focusing on auth.

from cryptography.fernet import Fernet, InvalidToken

# Initialize Fernet with the key from settings
# This should only happen once when the module is loaded.
CREDENTIALS_ENCRYPTION_KEY = settings.CREDENTIALS_ENCRYPTION_KEY
_fernet_instance = None

if CREDENTIALS_ENCRYPTION_KEY == "your_32_byte_url_safe_base64_encoded_key" or not CREDENTIALS_ENCRYPTION_KEY:
    print("WARNING: Using a default or missing CREDENTIALS_ENCRYPTION_KEY. API Key encryption will be INSECURE.")
    print("Please generate a key using 'from cryptography.fernet import Fernet; Fernet.generate_key().decode()' and set it in your config/environment.")
    # For sandbox/dev purposes ONLY, using a fixed insecure key if not set.
    # In a real production setup, the application should fail to start or use a securely managed key.
    _fernet_instance = Fernet(b'qgY_wCoIScUyMDRz5o9XytkGZ8N9C82mXN0p7xJReJM=') # Valid 32 url-safe base64 key
else:
    try:
        _fernet_instance = Fernet(CREDENTIALS_ENCRYPTION_KEY.encode())
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize Fernet with CREDENTIALS_ENCRYPTION_KEY: {e}")
        print("API Key encryption will NOT work. Please check your key.")
        # Application should ideally not run if encryption cannot be set up.
        # Forcing a fallback to an insecure key for sandbox to continue, THIS IS BAD FOR PROD.
        # Using a different valid key for the fallback to distinguish it.
        _fernet_instance = Fernet(b'fS3vXRIbZ4a5k2jX9sG0cH8dLpW7qY1oA6nUvI2cE4Y=') # Another valid key for fallback


def encrypt_data(data: Optional[str]) -> Optional[str]:
    if data is None:
        return None
    if not _fernet_instance:
        print("ERROR: Fernet instance not available for encryption. Data will not be encrypted.")
        # In a strict setup, this should raise an error.
        return data # Returning raw data is insecure if encryption fails.
    try:
        return _fernet_instance.encrypt(data.encode()).decode()
    except Exception as e:
        print(f"Error during encryption: {e}")
        # Depending on policy, either raise error or return None/original data with warning
        return None # Or raise an error

def decrypt_data(encrypted_data: Optional[str]) -> Optional[str]:
    if encrypted_data is None:
        return None
    if not _fernet_instance:
        print("ERROR: Fernet instance not available for decryption.")
        return None # Cannot decrypt
    try:
        return _fernet_instance.decrypt(encrypted_data.encode()).decode()
    except InvalidToken:
        print("Error during decryption: Invalid token or data. Possibly not encrypted or wrong key.")
        return None # Data might not be encrypted, or key is wrong
    except Exception as e:
        print(f"Error during decryption: {e}")
        return None # Or raise an error
