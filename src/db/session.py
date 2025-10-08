import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from supabase import create_client, Client
from src.core.config import settings

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
)

# Create async session factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    Use in FastAPI routes with: db: AsyncSession = Depends(get_db_session)
    """
    async with async_session_factory() as session:
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

