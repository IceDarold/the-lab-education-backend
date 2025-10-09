from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.services.user_service import UserService
from src.services.session_service import SessionService
from src.services.profile_service import ProfileService
from src.schemas import UserCreate, User, Token, RefreshTokenRequest, RefreshTokenResponse
from src.dependencies import get_db, get_current_user
from src.core.security import create_access_token, create_refresh_token, verify_refresh_token
from src.core.logging import get_logger
from src.core.errors import AuthenticationError, AuthorizationError, DatabaseError, ExternalServiceError, ValidationError, SupabaseTimeoutError, SupabaseCircuitBreakerError
from src.core.supabase_client import get_resilient_supabase_client, get_resilient_supabase_admin_client
from src.core.rate_limiting import auth_limiter, LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT, REFRESH_RATE_LIMIT
import uuid
from uuid import UUID

logger = get_logger(__name__)

router = APIRouter()

@router.options("/login")
async def options_login(request: Request):
    logger.info(f"OPTIONS request to /login from origin: {request.headers.get('origin')}, method: {request.method}, headers: {dict(request.headers)}")
    return {}

@router.post("/login", response_model=Token)
@auth_limiter.limit(LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    email = form_data.username
    logger.info(f"Login attempt for user: {email}")

    try:
        # Authenticate with Supabase
        supabase = get_resilient_supabase_client()
        auth_response = await supabase.auth.sign_in_with_password({
            "email": email,
            "password": form_data.password
        })

        if not auth_response.user:
            logger.warning(f"Invalid login credentials for user: {email}")
            raise AuthenticationError("Invalid email or password")

        user_id = str(auth_response.user.id)
        logger.info(f"Supabase authentication successful for user: {email}")

    except (SupabaseTimeoutError, SupabaseCircuitBreakerError) as e:
        logger.error(f"Supabase resilience error during login for user {email}: {str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable. Please try again later.")
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
        # Ensure profile exists (for backward compatibility with existing users)
        profile = await ProfileService.get_profile_by_id(user_id, db)
        if not profile:
            logger.info(f"Profile not found for user {email}, creating one")
            # We don't have full_name from Supabase, so we'll use a default
            await ProfileService.create_profile(
                profile_id=user_id,
                full_name=email.split('@')[0],  # Use email prefix as name
                email=email,
                role="student",
                db=db
            )
            logger.info(f"Profile created for existing user: {email}")

        # Create JWT tokens
        access_token = create_access_token(data={"sub": user_id, "email": email})
        refresh_token = create_refresh_token(data={"sub": user_id, "email": email})
        logger.debug(f"JWT tokens created for user: {email}")

        # Store refresh token in session
        client_ip = request.client.host if request else None
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise ValidationError(f"Invalid user ID format: {user_id}")
        await SessionService.create_session(
            db=db,
            user_id=user_uuid,
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
@auth_limiter.limit(REGISTER_RATE_LIMIT)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    email = user_data.email
    logger.info(f"Registration attempt for user: {email}")

    supabase = get_resilient_supabase_client()
    supabase_user_id = None
    profile_created = False
    user_created = False

    try:
        # Step 1: Create Supabase user first
        auth_response = await supabase.auth.sign_up({
            "email": email,
            "password": user_data.password
        })

        if not auth_response.user:
            logger.warning(f"Supabase registration failed for user: {email} - no user returned")
            raise ExternalServiceError("Failed to create user account with authentication service")

        supabase_user_id = str(auth_response.user.id)
        logger.info(f"Supabase user created with ID: {supabase_user_id}")

        # Step 2: Create profile in local DB with Supabase user ID
        profile = await ProfileService.create_profile(
            profile_id=supabase_user_id,
            full_name=user_data.full_name,
            email=email,
            role="student",
            db=db
        )
        profile_created = True
        logger.info(f"Profile created for user: {email}")

        # Step 3: Create user in local DB with same ID
        user = await UserService.create_user_with_id(supabase_user_id, user_data, db)
        user_created = True
        logger.info(f"Local user created for: {email}")

        # Step 4: Create access token
        access_token = create_access_token(data={"sub": supabase_user_id, "email": user.email})
        logger.info(f"Registration successful for user: {email}")
        return {"access_token": access_token, "token_type": "bearer"}

    except DatabaseError as e:
        logger.error(f"Database error during registration for user {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user account in database")
    except (SupabaseTimeoutError, SupabaseCircuitBreakerError) as e:
        logger.error(f"Supabase resilience error during registration for user {email}: {str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable. Please try again later.")
    except ExternalServiceError as e:
        logger.error(f"External service error during registration for user {email}: {str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error during registration for user {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed due to an unexpected error")

    finally:
        # Comprehensive rollback logic
        if not (profile_created and user_created):
            logger.warning(f"Rolling back partial registration for user {email}")

            # Rollback: delete Supabase user if created
            if supabase_user_id:
                try:
                    admin_supabase = get_resilient_supabase_admin_client()
                    await admin_supabase.admin.delete_user(supabase_user_id)
                    logger.info(f"Rolled back Supabase user for: {email}")
                except Exception as delete_e:
                    logger.error(f"Failed to rollback Supabase user {email}: {str(delete_e)}")

            # Rollback: delete profile if created
            if profile_created:
                try:
                    await ProfileService.delete_profile(supabase_user_id, db)
                    logger.info(f"Rolled back profile for: {email}")
                except Exception as delete_e:
                    logger.error(f"Failed to rollback profile {email}: {str(delete_e)}")

            # Rollback: delete local user if created
            if user_created:
                try:
                    await UserService.delete_user(supabase_user_id, db)
                    logger.info(f"Rolled back local user for: {email}")
                except Exception as delete_e:
                    logger.error(f"Failed to rollback local user {email}: {str(delete_e)}")

@router.post("/refresh", response_model=RefreshTokenResponse)
@auth_limiter.limit(REFRESH_RATE_LIMIT)
async def refresh_token(
    request: Request,
    request_data: RefreshTokenRequest,
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
        expires_in = 15 * 60  # 15 minutes
        expires_at = int((datetime.now(UTC).timestamp() + expires_in) * 1000)

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
