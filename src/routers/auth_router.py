from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user_service import UserService
from src.services.session_service import SessionService
from src.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest, RefreshTokenResponse
from src.dependencies import get_db, get_current_user
from src.core.security import create_access_token, create_refresh_token, verify_refresh_token
from src.db.session import get_supabase_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    # Authenticate with Supabase
    supabase = get_supabase_client()
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        user_id = str(auth_response.user.id)
        email = auth_response.user.email
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # Create JWT tokens
    access_token = create_access_token(data={"sub": user_id, "email": email})
    refresh_token = create_refresh_token(data={"sub": user_id, "email": email})

    # Store refresh token in session
    client_ip = request.client.host if request else None
    from uuid import UUID
    await SessionService.create_session(
        db=db,
        user_id=UUID(user_id),
        refresh_token=refresh_token,
        ip_address=client_ip
    )

    logger.info(f"User {email} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    supabase = get_supabase_client()
    try:
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        if auth_response.user:
            user = await UserService.create_user_with_id(str(auth_response.user.id), user_data, db)
            access_token = create_access_token(data={"sub": str(user.user_id), "email": user.email})
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Registration failed due to an internal error")

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request_data: RefreshTokenRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_refresh_token(request_data.refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Check if session exists and is active
        token_hash = SessionService.hash_refresh_token(request_data.refresh_token)
        session = await SessionService.get_session_by_token_hash(db, token_hash)

        if not session:
            logger.warning(f"Invalid refresh attempt for user {user_id}")
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Create new tokens
        access_token = create_access_token(data={"sub": user_id, "email": payload.get("email")})
        new_refresh_token = create_refresh_token(data={"sub": user_id, "email": payload.get("email")})

        # Update session with new refresh token
        new_token_hash = SessionService.hash_refresh_token(new_refresh_token)
        session.refresh_token_hash = new_token_hash
        session.ip_address = request.client.host if request else None
        await db.commit()

        # Calculate expiration times
        from datetime import datetime
        expires_in = 15 * 60  # 15 minutes
        expires_at = int((datetime.utcnow().timestamp() + expires_in) * 1000)

        logger.info(f"Token refreshed for user {user_id}")
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            expires_at=expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token generation failed")


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user