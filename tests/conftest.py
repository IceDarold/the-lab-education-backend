import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.rate_limiting import limiter
from src.routers.auth_router import router as auth_router
from tests.test_admin_router_no_auth import router as admin_router
from src.api.v1.lessons import router as lessons_router
from src.api.v1.courses import router as courses_router
from src.api.v1.dashboard import router as dashboard_router
from src.api.v1.quizzes import router as quizzes_router
from src.routers.health_router import router as health_router
from src.routers.analytics_router import router as analytics_router
from src.dependencies import get_fs_service, get_content_scanner, get_ulf_parser
from src.db.session import get_db
from src.core.security import get_current_user, get_current_admin


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables for all tests."""
    # Set test environment variables
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_KEY", "test-key")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-tokens")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
    os.environ.setdefault("ENVIRONMENT", "test")
    yield
    # Cleanup if needed


@pytest.fixture(scope="session")
def mock_db_session():
    """Mock AsyncSession database session (session scope for reuse)."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture(scope="session")
def mock_supabase_client():
    """Mock Supabase client (session scope for reuse)."""
    client = MagicMock()
    client.auth = MagicMock()
    client.auth.sign_in_with_password = AsyncMock()
    client.auth.sign_up = AsyncMock()
    client.auth.sign_out = AsyncMock()
    return client


@pytest.fixture(scope="session")
def mock_supabase_admin_client():
    """Mock Supabase admin client (session scope for reuse)."""
    client = MagicMock()
    client.admin = MagicMock()
    client.admin.delete_user = AsyncMock()
    return client


@pytest.fixture(scope="session")
def mock_user_service():
    """Mock UserService (session scope for reuse)."""
    service = MagicMock()
    service.create_user_with_id = AsyncMock()
    service.delete_user = AsyncMock()
    service.get_user_by_id = AsyncMock()
    service.get_user_by_email = AsyncMock()
    return service


@pytest.fixture(scope="session")
def mock_session_service():
    """Mock SessionService (session scope for reuse)."""
    service = MagicMock()
    service.create_session = AsyncMock()
    service.get_session_by_token_hash = AsyncMock()
    service.hash_refresh_token = MagicMock(return_value="hashed_token")
    service.delete_session = AsyncMock()
    return service


@pytest.fixture(scope="session")
def mock_fs_service():
    """Mock FileSystemService (session scope for reuse)."""
    service = MagicMock()
    service.read_file = AsyncMock(return_value="test content")
    service.write_file = AsyncMock()
    service.create_directory = AsyncMock()
    service.delete_file = AsyncMock()
    service.delete_directory = AsyncMock()
    service.path_exists = AsyncMock(return_value=True)
    service.scan_directory = AsyncMock(return_value=[])
    return service


@pytest.fixture(scope="session")
def mock_content_scanner(mock_fs_service):
    """Mock ContentScannerService (session scope for reuse)."""
    service = MagicMock()
    service.build_content_tree = AsyncMock()
    service.clear_cache = AsyncMock()
    return service


@pytest.fixture(scope="session")
def mock_ulf_parser():
    """Mock ULFParserService (session scope for reuse)."""
    service = MagicMock()
    service.parse = MagicMock(return_value={"title": "Test", "cells": []})
    return service


@pytest.fixture(scope="function")
def mock_current_user():
    """Mock authenticated user for tests."""
    from src.schemas.user import User
    from uuid import uuid4
    return User(
        user_id=uuid4(),
        full_name="Test User",
        email="test@example.com",
        role="student"
    )


@pytest.fixture(scope="function")
def mock_current_admin():
    """Mock admin user for tests."""
    from src.schemas.user import User
    from uuid import uuid4
    return User(
        user_id=uuid4(),
        full_name="Admin User",
        email="admin@example.com",
        role="admin"
    )


@pytest.fixture(scope="function")
def test_app(mock_db_session, mock_supabase_client, mock_supabase_admin_client,
              mock_user_service, mock_session_service, mock_fs_service, mock_content_scanner, mock_ulf_parser,
              mock_current_user, mock_current_admin, monkeypatch):
    """Create test FastAPI app with mocked dependencies and correct router prefixes."""
    # Patch the oauth2_scheme at module level
    from src.core import security
    monkeypatch.setattr(security, 'oauth2_scheme', lambda: "dummy_token")

    app = FastAPI(title="Test API")
    app.state.limiter = limiter

    # Include routers with correct prefixes
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
    app.include_router(courses_router, prefix="/api/v1/courses", tags=["courses"])
    app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
    app.include_router(lessons_router, prefix="/api/v1/lessons", tags=["lessons"])
    app.include_router(quizzes_router, prefix="/api/v1/quizzes", tags=["quizzes"])
    app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

    # Mock dependencies
    app.dependency_overrides = {
        get_db: lambda: mock_db_session,
        get_fs_service: lambda: mock_fs_service,
        get_content_scanner: lambda: mock_content_scanner,
        get_ulf_parser: lambda: mock_ulf_parser,
        get_current_user: lambda: mock_current_user,
        get_current_admin: lambda: mock_current_admin,
    }

    return app


@pytest.fixture(scope="function")
def integration_app(mock_fs_service, mock_content_scanner, mock_ulf_parser):
    """Create integration test app with mocked services."""
    test_app = FastAPI()

    # Include the real routers
    test_app.include_router(admin_router, prefix="/api/admin")
    test_app.include_router(lessons_router, prefix="/api/lessons")
    test_app.include_router(courses_router, prefix="/api/courses")
    test_app.include_router(dashboard_router, prefix="/api/dashboard")
    test_app.include_router(quizzes_router, prefix="/api/quizzes")

    # Override dependencies
    test_app.dependency_overrides = {
        get_fs_service: lambda: mock_fs_service,
        get_content_scanner: lambda: mock_content_scanner,
        get_ulf_parser: lambda: mock_ulf_parser,
    }
    return test_app


@pytest.fixture(scope="function")
async def async_client(test_app):
    """Async test client for API testing."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def client(integration_app):
    """Synchronous test client for integration tests."""
    return TestClient(integration_app)