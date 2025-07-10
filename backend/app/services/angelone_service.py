# backend/app/services/angelone_service.py
from typing import Optional, Dict, Any, Tuple, List # Added List
from sqlalchemy.orm import Session

# Assuming 'smartapi-python' is the correct SDK name and it's installed.
# Actual import might vary based on the exact SDK version and structure.
try:
    from smartapi import SmartConnect # Common class name for AngelOne SDK
    # from smartapi.smartExceptions import SmartAPIException # Example exception
except ImportError:
    # This allows the application to run even if the SDK is not installed,
    # but service calls will fail. Useful for initial dev or if SDK is optional.
    SmartConnect = None
    # SmartAPIException = Exception # Fallback exception
    print("WARNING: AngelOne SmartAPI SDK (smartapi-python) not found. AngelOneService will not function.")


from backend.app import models, schemas, crud
from backend.core.security import decrypt_data, encrypt_data
from backend.core.config import settings # For API Key if it's global, though user-specific is better

class AngelOneServiceError(Exception):
    """Custom exception for AngelOneService errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AngelOneService:
    def __init__(self, db: Session, user: models.User):
        self.db = db
        self.user = user
        self.smart_connect: Optional[SmartConnect] = None

        if not SmartConnect:
            raise AngelOneServiceError("AngelOne SDK not available.", status_code=503)

        # Decrypt user-specific API credentials
        self.api_key = decrypt_data(user.api_key_encrypted)
        self.client_id = user.broker_user_id # Assumed to be AngelOne Client ID
        # API Secret is often used directly by SDK or for token exchange, not always for SmartConnect init
        self.api_secret = decrypt_data(user.api_secret_encrypted)

        if not self.api_key or not self.client_id:
            raise AngelOneServiceError("AngelOne API key or Client ID not configured for the user.", status_code=400)

        self.smart_connect = SmartConnect(api_key=self.api_key)
        # Load existing session token if available and potentially valid
        self.session_token = decrypt_data(user.access_token_encrypted)
        if self.session_token:
            self.smart_connect.setAccessToken(self.session_token) # Method name might vary
            # TODO: Add logic to check token validity (e.g. by making a test call or if SDK provides it)

    async def _ensure_session(self, user_pin_or_password: Optional[str] = None, totp: Optional[str] = None) -> bool:
        """
        Ensures an active AngelOne session.
        Attempts to use existing token, then refresh, then generate new session.
        This is a simplified version. Real implementation needs robust token validity checks.
        """
        if self.smart_connect is None: return False # Should not happen if constructor succeeded

        # 1. Check if current session_token is valid (e.g., by a test API call or SDK method)
        #    For simplicity, we'll assume it needs regeneration if not present or if a call fails.
        #    A more robust check would be to see if smart_connect.getProfile() works.
        #    If self.session_token is None, we definitely need to generate one.

        if self.session_token:
             # Try a lightweight call to check token validity, e.g., getProfile
            try:
                profile_test = self.smart_connect.getProfile()
                if profile_test and profile_test.get("status"): # Check for successful response
                    print("AngelOne session token is valid.")
                    return True
                else:
                    print("AngelOne session token seems invalid, attempting to regenerate.")
                    self.session_token = None # Force regeneration
            except Exception as e: # Catch specific SDK exceptions for token invalidity
                print(f"AngelOne session token validation failed: {e}. Attempting to regenerate.")
                self.session_token = None # Force regeneration

        # If no valid session token, try to generate a new one
        if not self.session_token:
            if not user_pin_or_password or not totp:
                # This indicates that the calling context (e.g., an API endpoint)
                # needs to somehow obtain these from the user if a new session is required.
                # For background tasks, this won't work without stored credentials or a different flow.
                raise AngelOneServiceError(
                    "AngelOne session requires password/PIN and TOTP for generation.",
                    status_code=401 # Unauthorized or requires further credentials
                )

            print(f"Attempting to generate new AngelOne session for client {self.client_id}...")
            try:
                # The generateSession method in smartapi-python typically requires client_code, password, totp
                session_data = self.smart_connect.generateSession(
                    self.client_id,
                    user_pin_or_password,
                    totp
                )

                if session_data and session_data.get("status") and session_data.get("data"):
                    self.session_token = session_data["data"].get("jwtToken")
                    refresh_token = session_data["data"].get("refreshToken")
                    # feed_token = session_data["data"].get("feedToken") # For market feeds

                    if not self.session_token:
                        raise AngelOneServiceError("Failed to retrieve jwtToken from AngelOne session data.", status_code=500)

                    self.smart_connect.setAccessToken(self.session_token) # Update SDK instance

                    # Encrypt and store new tokens
                    self.user.access_token_encrypted = encrypt_data(self.session_token)
                    self.user.refresh_token_encrypted = encrypt_data(refresh_token) if refresh_token else None

                    self.db.add(self.user)
                    self.db.commit()
                    print("New AngelOne session generated and tokens stored.")
                    return True
                else:
                    error_message = session_data.get("message", "Unknown error during session generation.")
                    raise AngelOneServiceError(f"AngelOne session generation failed: {error_message}", status_code=401)

            except Exception as e: # Catch specific SDK exceptions if possible
                # Example: SmartAPIException as e
                raise AngelOneServiceError(f"Error during AngelOne session generation: {str(e)}", status_code=500)

        return False # Should have returned True if session established

    async def get_profile_and_funds(self, pin_for_session: Optional[str] = None, totp_for_session: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetches user profile and fund details from AngelOne."""
        if self.smart_connect is None: return None

        await self._ensure_session(pin_for_session, totp_for_session) # Ensure session is active

        try:
            profile_data = self.smart_connect.getProfile() # Method name from typical SDK
            if profile_data and profile_data.get("status"):
                return profile_data.get("data")
            else:
                error_msg = profile_data.get("message", "Failed to fetch profile.")
                print(f"AngelOne get_profile error: {error_msg}")
                # If token expired, _ensure_session should ideally handle it, or we try once more.
                # For now, just raise based on current response.
                if profile_data.get("errorcode") == "AG8001": # Example for session expired
                    self.session_token = None # Clear token
                    self.user.access_token_encrypted = None # Clear stored token
                    self.db.commit()
                    raise AngelOneServiceError("AngelOne session expired. Please try again to re-login.", status_code=401)
                raise AngelOneServiceError(error_msg, status_code=502) # Bad Gateway if API call failed
        except Exception as e:
            print(f"Exception in get_profile_and_funds: {e}")
            raise AngelOneServiceError(f"Failed to fetch profile from AngelOne: {str(e)}", status_code=500)

    async def get_holdings(self, pin_for_session: Optional[str] = None, totp_for_session: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Fetches user's stock holdings from AngelOne."""
        if self.smart_connect is None: return None

        await self._ensure_session(pin_for_session, totp_for_session)

        try:
            holdings_data = self.smart_connect.getHolding() # Method name from typical SDK
            if holdings_data and holdings_data.get("status"):
                return holdings_data.get("data") # Usually a list of holding dicts
            else:
                error_msg = holdings_data.get("message", "Failed to fetch holdings.")
                print(f"AngelOne get_holdings error: {error_msg}")
                if holdings_data.get("errorcode") == "AG8001": # Session expired
                    self.session_token = None
                    self.user.access_token_encrypted = None
                    self.db.commit()
                    raise AngelOneServiceError("AngelOne session expired. Please try again to re-login.", status_code=401)
                raise AngelOneServiceError(error_msg, status_code=502)
        except Exception as e:
            print(f"Exception in get_holdings: {e}")
            raise AngelOneServiceError(f"Failed to fetch holdings from AngelOne: {str(e)}", status_code=500)

    # TODO: Implement other methods like get_positions, get_order_book, place_order etc.
    # TODO: Implement token refresh logic if AngelOne provides refresh tokens and SDK supports it.
    #       The smart_connect.refreshToken() method might exist.

# Example (conceptual) of how this service might be used in an endpoint:
# async def get_angelone_profile_endpoint(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
#     # The endpoint would need to handle how it gets user_pin and totp if a new session is needed.
#     # This could be from a short-lived cache after user input, or a modal in frontend.
#     # For now, this service requires them if a session is not already active or valid.
#     user_pin = "USER_PIN_FROM_SOMEWHERE" # This is the tricky part for automated calls
#     user_totp = "USER_TOTP_FROM_SOMEWHERE"
#     service = AngelOneService(db=db, user=current_user)
#     try:
#         profile = await service.get_profile_and_funds(user_pin_or_password=user_pin, totp=user_totp)
#         return profile
#     except AngelOneServiceError as e:
#         raise HTTPException(status_code=e.status_code, detail=e.message)
