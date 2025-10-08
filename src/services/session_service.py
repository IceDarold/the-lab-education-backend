import hashlib
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from src.models.user_session import UserSession
from src.core.security import create_refresh_token
from src.core.config import settings


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
        return session

    @staticmethod
    async def get_session_by_token_hash(db: AsyncSession, token_hash: str) -> Optional[UserSession]:
        """Get session by refresh token hash"""
        query = select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def invalidate_session(db: AsyncSession, session_id: UUID) -> bool:
        """Invalidate a session"""
        query = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(is_active=False)
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def invalidate_user_sessions(db: AsyncSession, user_id: UUID) -> int:
        """Invalidate all sessions for a user"""
        query = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_active == True)
            .values(is_active=False)
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions"""
        query = (
            update(UserSession)
            .where(UserSession.expires_at <= datetime.utcnow(), UserSession.is_active == True)
            .values(is_active=False)
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount