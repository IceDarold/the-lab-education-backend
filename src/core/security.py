from uuid import UUID
import logging
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.core.config import settings
from src.core.errors import AuthenticationError, AuthorizationError, ValidationError
from src.db.session import get_supabase_client, get_supabase_admin_client
from src.schemas.user import User

logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # Default 7 days
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise AuthenticationError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Refresh token expired")
    except jwt.exceptions.DecodeError:
        raise AuthenticationError("Invalid refresh token")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != "access":
            raise AuthenticationError("Invalid token type")
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            raise AuthenticationError("Invalid token payload")
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.exceptions.DecodeError:
        raise AuthenticationError("Invalid authentication credentials")

    # For now, return basic user info from token
    # TODO: Fetch full profile from database
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValidationError(f"Invalid user ID format: {user_id}")

    return User(
        user_id=user_uuid,
        full_name="",  # Would fetch from DB
        email=email,
        role="student",  # Would fetch from DB
    )


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise AuthorizationError("Admin access required")
    return current_user

