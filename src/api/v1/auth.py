import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import get_current_user
from src.core.supabase_client import get_resilient_supabase_admin_client, get_resilient_supabase_client
from src.schemas.token import Token
from src.schemas.user import CheckEmailRequest, ForgotPasswordRequest, ResetPasswordRequest, User, UserCreate
from src.core.logging import get_logger
from src.core.config import settings

router = APIRouter()
logger = get_logger(__name__)


def get_supabase_client():
    """Backward compatible wrapper so tests can patch the legacy helper."""
    return get_resilient_supabase_client()


def get_supabase_admin_client():
    """Backward compatible wrapper so tests can patch the legacy helper."""
    return get_resilient_supabase_admin_client()


async def _finalize_request(result: Any) -> Any:
    if asyncio.iscoroutine(result):
        return await result

    execute = getattr(result, "execute", None)
    if callable(execute):
        exec_result = execute()
        if asyncio.iscoroutine(exec_result):
            return await exec_result
        return exec_result

    return result


@router.post("/register", response_model=None, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    supabase = get_supabase_client()

    try:
        response = await _finalize_request(
            supabase.auth.sign_up(
            {
                "email": user_in.email,
                "password": user_in.password,
                "options": {"data": {"full_name": user_in.full_name}},
            }
            )
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed",
        ) from exc

    session = getattr(response, "session", None)
    user = getattr(response, "user", None)
    token = getattr(session, "access_token", None)
    if not session or not token:
        # User may be created but email confirmation is required
        if user is not None:
            return {"status": "pending_confirmation"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed",
        )

    profile_payload: Dict[str, Any] = {
        "full_name": user_in.full_name,
        "email": user_in.email,
    }
    if user and getattr(user, "id", None):
        profile_payload["id"] = getattr(user, "id")

    profiles_table = supabase.table("profiles")
    try:
        await _finalize_request(profiles_table.insert(profile_payload))
    except Exception:  # pragma: no cover - avoid failing signup when profile insert fails
        pass

    return Token(access_token=token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    supabase = get_supabase_client()

    try:
        response = await _finalize_request(
            supabase.auth.sign_in_with_password(
                {
                    "email": form_data.username,
                    "password": form_data.password,
                }
            )
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    session = getattr(response, "session", None)
    token = getattr(session, "access_token", None)
    if not session or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

@router.post("/check-email")
async def check_email(request: CheckEmailRequest):
    supabase = get_supabase_admin_client()

    try:
        profile_response = await _finalize_request(
            supabase.table("profiles").select("id").eq("email", request.email).execute()
        )
        exists = bool(getattr(profile_response, "data", []))
        return {"exists": exists}
    except Exception as exc:
        logger.exception("Failed to check email existence for '%s'", request.email)
        error_detail: Any = "Database error"
        if settings.DEBUG:
            error_detail = {"message": "Database error", "error": str(exc)}
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from exc


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    supabase = get_supabase_admin_client()

    # Check if email exists in profiles
    try:
        profile_response = await _finalize_request(
            supabase.table("profiles").select("id").eq("email", request.email).execute()
        )
        exists = bool(getattr(profile_response, "data", []))
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to verify email existence during forgot-password for '%s'", request.email)
        error_detail: Any = "Database error"
        if settings.DEBUG:
            error_detail = {"message": "Database error", "error": str(exc)}
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from exc

    # Send reset email using regular client
    supabase_auth = get_supabase_client()
    try:
        await _finalize_request(
            supabase_auth.auth.reset_password_for_email(request.email)
        )
        return {"message": "Password reset email sent"}
    except Exception as exc:
        logger.exception("Failed to send reset password email for '%s'", request.email)
        error_detail: Any = "Failed to send reset email"
        if settings.DEBUG:
            error_detail = {"message": "Failed to send reset email", "error": str(exc)}
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from exc


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    supabase = get_supabase_client()

    # Verify the recovery token
    try:
        verify_response = await _finalize_request(
            supabase.auth.verify_otp(type='recovery', token=request.token)
        )
        # If successful, the session is set
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        ) from exc

    # Update the password
    try:
        await _finalize_request(
            supabase.auth.update_user({"password": request.new_password})
        )
        return {"message": "Password updated successfully"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        ) from exc
