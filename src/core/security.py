from uuid import UUID
import logging
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.core.config import settings
from src.db.session import get_supabase_client, get_supabase_admin_client
from src.schemas.user import User

logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    supabase = get_supabase_client()
    try:
        response = supabase.auth.get_user(token)
        logger.info("Token validation successful")
    except Exception as exc:  # pragma: no cover - defensive against SDK internals
        logger.error(f"Token validation failed: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = getattr(response, "user", None)
    if not user:
        logger.error("No user found in response")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info("User found")

    metadata = getattr(user, "user_metadata", {}) or {}
    full_name = metadata.get("full_name") or metadata.get("name") or metadata.get("fullName") or ""

    # Fetch role from profiles table
    user_id = str(getattr(user, "id"))
    logger.info("Fetching profile for user")
    try:
        admin_supabase = get_supabase_admin_client()
        profile_response = admin_supabase.table("profiles").select("role").eq("id", user_id).execute()
        profile_data = getattr(profile_response, "data", []) or []
        role = profile_data[0].get("role", "student") if profile_data else "student"
    except Exception as exc:
        logger.error(f"Profile query failed: {str(exc)}")
        logger.error(f"Exception type: {type(exc)}")
        role = "student"

    return User(
        user_id=UUID(user_id),
        full_name=full_name,
        email=getattr(user, "email"),
        role=role,
    )


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

