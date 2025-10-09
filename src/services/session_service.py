import hashlib
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError

from src.models.user_session import UserSession
from src.core.security import create_refresh_token
from src.core.config import settings
from src.core.errors import DatabaseError, ValidationError
from src.core.logging import get_logger
from src.core.utils import maybe_await

logger = get_logger(__name__)


class SessionService:
    @staticmethod
    def hash_refresh_token(token: str) -> str:
        """Hash refresh token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: UUID,
        refresh_token: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> UserSession:
        """Create a new user session"""
        logger.debug(f"Creating session for user: {user_id}")
        try:
            if not refresh_token:
                raise ValidationError("Refresh token is required")

            if expires_delta is None:
                expires_delta = timedelta(days=7)

            expires_at = datetime.utcnow() + expires_delta
            token_hash = SessionService.hash_refresh_token(refresh_token)

            session = UserSession(
                user_id=user_id,
                refresh_token_hash=token_hash,
                device_info=device_info,
                ip_address=ip_address,
                expires_at=expires_at
            )

            db.add(session)
            await db.commit()
            await db.refresh(session)
            logger.info(f"Successfully created session for user: {user_id}")
            return session

        except ValidationError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error creating session for user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to create session: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating session for user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during session creation: {str(e)}")

    @staticmethod
    async def get_session_by_token_hash(db: AsyncSession, token_hash: str) -> Optional[UserSession]:
        """Get session by refresh token hash"""
        logger.debug("Looking up session by token hash")
        try:
            query = select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
            result = await db.execute(query)
            session = await maybe_await(result.scalar_one_or_none())
            if session:
                logger.debug(f"Found active session for user: {session.user_id}")
            else:
                logger.debug("No active session found for token hash")
            return session
        except SQLAlchemyError as e:
            logger.error(f"Database error looking up session: {str(e)}")
            raise DatabaseError(f"Failed to lookup session: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error looking up session: {str(e)}")
            raise DatabaseError(f"Unexpected error during session lookup: {str(e)}")

    @staticmethod
    async def invalidate_session(db: AsyncSession, session_id: UUID) -> bool:
        """Invalidate a session"""
        logger.debug(f"Invalidating session: {session_id}")
        try:
            query = (
                update(UserSession)
                .where(UserSession.id == session_id)
                .values(is_active=False)
            )
            result = await db.execute(query)
            await db.commit()
            invalidated = result.rowcount > 0
            if invalidated:
                logger.info(f"Successfully invalidated session: {session_id}")
            else:
                logger.warning(f"Session not found for invalidation: {session_id}")
            return invalidated
        except SQLAlchemyError as e:
            logger.error(f"Database error invalidating session {session_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to invalidate session: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error invalidating session {session_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during session invalidation: {str(e)}")

    @staticmethod
    async def invalidate_user_sessions(db: AsyncSession, user_id: UUID) -> int:
        """Invalidate all sessions for a user"""
        logger.info(f"Invalidating all sessions for user: {user_id}")
        try:
            query = (
                update(UserSession)
                .where(UserSession.user_id == user_id, UserSession.is_active == True)
                .values(is_active=False)
            )
            result = await db.execute(query)
            await db.commit()
            count = result.rowcount
            logger.info(f"Invalidated {count} sessions for user: {user_id}")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error invalidating sessions for user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to invalidate user sessions: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error invalidating sessions for user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during user session invalidation: {str(e)}")

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions"""
        logger.debug("Cleaning up expired sessions")
        try:
            query = (
                update(UserSession)
                .where(UserSession.expires_at <= datetime.utcnow(), UserSession.is_active == True)
                .values(is_active=False)
            )
            result = await db.execute(query)
            await db.commit()
            count = result.rowcount
            logger.info(f"Cleaned up {count} expired sessions")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error cleaning up expired sessions: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to cleanup expired sessions: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error cleaning up expired sessions: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during session cleanup: {str(e)}")
