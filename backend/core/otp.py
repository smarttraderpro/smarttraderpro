# backend/core/otp.py
import random
import string
from datetime import datetime, timedelta, timezone
from backend.core.config import settings

def generate_otp(length: int = 6) -> str:
    """Generates a random OTP of specified length."""
    # characters = string.ascii_uppercase + string.digits # Alphanumeric
    characters = string.digits # Numeric only
    otp = "".join(random.choice(characters) for _ in range(length))
    return otp

def is_otp_expired(otp_sent_at: datetime) -> bool:
    """Checks if the OTP has expired based on settings.OTP_EXPIRY_MINUTES."""
    if not otp_sent_at:
        return True # If not sent, effectively expired or invalid
    # Ensure otp_sent_at is offset-aware if it's not already
    if otp_sent_at.tzinfo is None:
        # Assuming otp_sent_at was stored in UTC if naive
        otp_sent_at = otp_sent_at.replace(tzinfo=timezone.utc)

    expiry_duration = timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    return datetime.now(timezone.utc) > (otp_sent_at + expiry_duration)

# Placeholder for sending OTP via email/SMS
# In a real application, these would use services like SendGrid, Twilio, etc.

def send_otp_email(email_to: str, otp: str):
    """Simulates sending OTP via email."""
    # TODO: Integrate with an actual email service
    print(f"Simulating sending OTP to email: {email_to}, OTP: {otp}")
    return True # Simulate success

def send_otp_sms(mobile_to: str, otp: str):
    """Simulates sending OTP via SMS."""
    # TODO: Integrate with an actual SMS gateway
    print(f"Simulating sending OTP to mobile: {mobile_to}, OTP: {otp}")
    return True # Simulate success
