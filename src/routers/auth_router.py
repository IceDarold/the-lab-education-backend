from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user_service import UserService
from src.services.session_service import SessionService
from src.schemas import UserCreate, User, Token, RefreshTokenRequest, RefreshTokenResponse
from src.dependencies import get_db, get_current_user
from src.core.security import create_access_token, create_refresh_token, verify_refresh_token
from src.core.logging import get_logger
from src.core.errors import AuthenticationError, AuthorizationError, DatabaseError, ExternalServiceError
from src.db.session import get_supabase_client
from src.db.session import get_supabase_admin_client
import uuid

logger = get_logger(__name__)

router = APIRouter()

@router.options("/login")
async def options_login(request: Request):
    logger.info(f"OPTIONS request to /login from origin: {request.headers.get('origin')}, method: {request.method}, headers: {dict(request.headers)}")
    return {}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    email = form_data.username
    logger.info(f"Login attempt for user: {email}")

    try:
        # Authenticate with Supabase
        supabase = get_supabase_client()
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": form_data.password
        })

        if not auth_response.user:
            logger.warning(f"Invalid login credentials for user: {email}")
            raise AuthenticationError("Invalid email or password")

        user_id = str(auth_response.user.id)
        logger.info(f"Supabase authentication successful for user: {email}")

    except ExternalServiceError as e:
        logger.error(f"Supabase service error during login for user {email}: {str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable. Please try again later.")
    except AuthenticationError as e:
        logger.warning(f"Authentication failed for user {email}: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except Exception as e:
        logger.error(f"Unexpected error during login for user {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during login")

    try:
        # Create JWT tokens
        access_token = create_access_token(data={"sub": user_id, "email": email})
        refresh_token = create_refresh_token(data={"sub": user_id, "email": email})
        logger.debug(f"JWT tokens created for user: {email}")

        # Store refresh token in session
        client_ip = request.client.host if request else None
        from uuid import UUID
        await SessionService.create_session(
            db=db,
            user_id=UUID(user_id),
            refresh_token=refresh_token,
            ip_address=client_ip
        )
        logger.info(f"Session created for user: {email}")

    except DatabaseError as e:
        logger.error(f"Database error creating session for user {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user session")
    except Exception as e:
        logger.error(f"Unexpected error creating tokens/session for user {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete login process")

    logger.info(f"User {email} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    email = user_data.email
    logger.info(f"Registration attempt for user: {email}")

    supabase = get_supabase_client()
    user_id = str(uuid.uuid4())
    supabase_user_created = False
    local_user_created = False

    try:
        # Create local user first
        user = await UserService.create_user_with_id(user_id, user_data, db)
        local_user_created = True
        logger.info(f"Local user created for: {email}")

        # Then register with Supabase
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": user_data.password
        })

        if auth_response.user:
            supabase_user_created = True
            logger.info(f"Supabase user created for: {email}")
            access_token = create_access_token(data={"sub": str(user.user_id), "email": user.email})
            logger.info(f"Registration successful for user: {email}")
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            logger.warning(f"Supabase registration failed for user: {email} - no user returned")
            raise ExternalServiceError("Failed to create user account with authentication service")

    except DatabaseError as e:
        logger.error(f"Database error during registration for user {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user account in database")
    except ExternalServiceError as e:
        logger.error(f"External service error during registration for user {email}: {str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error during registration for user {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed due to an unexpected error")

    finally:
        # Rollback logic in case of failure
        if not supabase_user_created or not local_user_created:
            logger.warning(f"Rolling back registration for user {email}")

            # Rollback: delete from Supabase if created
            if supabase_user_created:
                try:
                    admin_supabase = get_supabase_admin_client()
                    admin_supabase.admin.delete_user(user_id)
                    logger.info(f"Rolled back Supabase user for: {email}")
                except Exception as delete_e:
                    logger.error(f"Failed to rollback Supabase user {email}: {str(delete_e)}")

            # Delete local user if created
            if local_user_created:
                try:
                    await UserService.delete_user(user_id, db)
                    logger.info(f"Rolled back local user for: {email}")
                except Exception as delete_e:
                    logger.error(f"Failed to rollback local user {email}: {str(delete_e)}")

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request_data: RefreshTokenRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    logger.info("Token refresh attempt")

    try:
        # Verify refresh token
        payload = verify_refresh_token(request_data.refresh_token)
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            logger.warning("Refresh token missing user ID")
            raise AuthenticationError("Invalid refresh token")

        logger.debug(f"Refresh token verified for user: {user_id}")

        # Check if session exists and is active
        token_hash = SessionService.hash_refresh_token(request_data.refresh_token)
        session = await SessionService.get_session_by_token_hash(db, token_hash)

        if not session:
            logger.warning(f"Session not found for refresh token hash for user {user_id}")
            raise AuthenticationError("Invalid or expired refresh token")

        logger.debug(f"Session validated for user: {user_id}")

        # Create new tokens
        access_token = create_access_token(data={"sub": user_id, "email": email})
        new_refresh_token = create_refresh_token(data={"sub": user_id, "email": email})
        logger.debug(f"New tokens generated for user: {user_id}")

        # Update session with new refresh token
        new_token_hash = SessionService.hash_refresh_token(new_refresh_token)
        session.refresh_token_hash = new_token_hash
        session.ip_address = request.client.host if request else None
        await db.commit()
        logger.debug(f"Session updated for user: {user_id}")

        # Calculate expiration times
        from datetime import datetime
        expires_in = 15 * 60  # 15 minutes
        expires_at = int((datetime.utcnow().timestamp() + expires_in) * 1000)

        logger.info(f"Token refresh successful for user: {user_id}")
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            expires_at=expires_at
        )

    except AuthenticationError as e:
        logger.warning(f"Authentication error during token refresh: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    except DatabaseError as e:
        logger.error(f"Database error during token refresh: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh token due to database error")
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed due to an unexpected error")


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user