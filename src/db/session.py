import os
from typing import AsyncGenerator, Optional, Callable, TypeVar, Awaitable
from contextlib import asynccontextmanager
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from supabase import create_client, Client
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Global variables for lazy loading
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[sessionmaker] = None


def get_database_engine() -> AsyncEngine:
    """
    Lazy initialization of database engine.
    Creates the engine on first access to prevent import-time failures.
    """
    global _engine
    if _engine is None:
        database_url = settings.DATABASE_URL
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        _engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging
            future=True,
            # Connection pooling configuration for better performance
            pool_size=10,  # Number of connections to maintain
            max_overflow=20,  # Maximum number of connections beyond pool_size
            pool_timeout=30,  # Timeout for getting a connection from pool
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before use
        )
    return _engine


def get_async_session_factory() -> sessionmaker:
    """
    Lazy initialization of async session factory.
    """
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_database_engine()
        _async_session_factory = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    Use in FastAPI routes with: db: AsyncSession = Depends(get_db_session)
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Alias for get_db_session for backward compatibility.
    """
    return get_db_session()


from supabase import create_client, Client
from src.core.config import settings


def get_supabase_client() -> Client:
    """
    Create the client inside the function to ensure compatibility with the serverless
    environment. This guarantees that for each "cold" function call, a new, fresh client is created.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    """
    Create a client with service role key for administrative operations,
    such as checking email existence without RLS restrictions.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for admin operations")
    return create_client(url, key)

