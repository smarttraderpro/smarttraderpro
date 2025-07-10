# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.core.security import verify_token
from backend.app import crud, models, schemas
from backend.db.session import get_db
from backend.core.config import settings

# This is the URL where the client can get a token (e.g., /api/v1/auth/login)
# It's used by FastAPI's interactive documentation (Swagger UI) for authorization.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = verify_token(token, expected_type="access") # verify_token returns subject (email)
    if email is None:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception # User not found for the email in token

    # Optionally, check if user is active
    # if not user.is_active:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# Dependency for admin users (example)
# async def get_current_admin_user(
#     current_user: models.User = Depends(get_current_active_user)
# ) -> models.User:
#     if current_user.role != models.UserRole.ADMIN:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="The user doesn't have enough privileges"
#         )
#     return current_user

from typing import Union, List

def require_role(required_role: Union[models.UserRole, List[models.UserRole]]):
    """
    Dependency that checks if the current active user has the required role(s).
    """
    async def role_checker(current_user: models.User = Depends(get_current_active_user)) -> models.User:
        if isinstance(required_role, list):
            if current_user.role not in required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User does not have the required roles. Must be one of: {', '.join(r.value for r in required_role)}"
                )
        elif current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required role: {required_role.value}"
            )
        return current_user
    return role_checker
