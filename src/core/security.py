from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.db.session import get_supabase_client
from src.schemas.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    supabase = get_supabase_client()
    try:
        response = await supabase.auth.get_user(token)
    except Exception as exc:  # pragma: no cover - defensive against SDK internals
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = getattr(response, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    metadata = getattr(user, "user_metadata", {}) or {}
    full_name = metadata.get("full_name") or metadata.get("name") or metadata.get("fullName") or ""

    # Fetch role from profiles table
    user_id = str(getattr(user, "id"))
    profile_response = supabase.table("profiles").select("role").eq("id", user_id).execute()
    profile_data = getattr(profile_response, "data", []) or []
    role = profile_data[0].get("role", "student") if profile_data else "student"

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

