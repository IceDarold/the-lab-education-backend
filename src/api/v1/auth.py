import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import get_current_user
from src.db.session import get_supabase_client
from src.schemas.token import Token
from src.schemas.user import CheckEmailRequest, ForgotPasswordRequest, ResetPasswordRequest, User, UserCreate

router = APIRouter()


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
    supabase = get_supabase_client()

    try:
        response = await _finalize_request(
            supabase.table("profiles").select("email").eq("email", request.email).execute()
        )
        exists = len(response.data) > 0
        return {"exists": exists}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    supabase = get_supabase_client()

    # Check if email exists in profiles
    try:
        response = await _finalize_request(
            supabase.table("profiles").select("email").eq("email", request.email).execute()
        )
        exists = len(response.data) > 0
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc

    # Send reset email
    try:
        await _finalize_request(
            supabase.auth.reset_password_for_email(request.email)
        )
        return {"message": "Password reset email sent"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email",
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
            supabase.auth.update_user({"password": request.newPassword})
        )
        return {"message": "Password updated successfully"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        ) from exc