import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

from src.core.rate_limiting import limiter
from src.routers.auth_router import router as auth_router
from src.schemas.user import UserCreate
from src.schemas.token import RefreshTokenRequest


@pytest.fixture
def mock_db():
    """Mock AsyncSession database."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    client = MagicMock()
    client.auth = MagicMock()
    return client


@pytest.fixture
def mock_supabase_admin_client():
    """Mock Supabase admin client."""
    client = MagicMock()
    client.admin = MagicMock()
    return client


@pytest.fixture
def mock_user_service():
    """Mock UserService."""
    service = MagicMock()
    service.create_user_with_id = AsyncMock()
    service.delete_user = AsyncMock()
    return service


@pytest.fixture
def mock_session_service():
    """Mock SessionService."""
    service = MagicMock()
    service.create_session = AsyncMock()
    service.get_session_by_token_hash = AsyncMock()
    service.hash_refresh_token = MagicMock(return_value="hashed_token")
    return service


@pytest.fixture
def mock_security_functions():
    """Mock security functions."""
    with patch('src.routers.auth_router.create_access_token', return_value="access_token") as mock_access, \
         patch('src.routers.auth_router.create_refresh_token', return_value="refresh_token") as mock_refresh, \
         patch('src.routers.auth_router.verify_refresh_token', return_value={"sub": "user_id", "email": "test@example.com"}) as mock_verify:
        yield {
            'create_access_token': mock_access,
            'create_refresh_token': mock_refresh,
            'verify_refresh_token': mock_verify
        }


@pytest.fixture
def test_app(mock_db, mock_supabase_client, mock_supabase_admin_client, mock_user_service, mock_session_service, mock_security_functions):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(auth_router, prefix="/auth")

    # Mock dependencies
    app.dependency_overrides = {
        "src.routers.auth_router.get_db": lambda: mock_db,
        "src.routers.auth_router.get_supabase_client": lambda: mock_supabase_client,
        "src.routers.auth_router.get_supabase_admin_client": lambda: mock_supabase_admin_client,
    }

    # Mock services
    with patch('src.routers.auth_router.UserService', mock_user_service), \
         patch('src.routers.auth_router.SessionService', mock_session_service):
        yield app


@pytest.fixture
async def async_client(test_app):
    """Async test client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, async_client, mock_supabase_client, mock_session_service, mock_security_functions, mock_db):
        """Test successful login."""
        # Mock Supabase auth response
        auth_response = MagicMock()
        auth_response.user = MagicMock()
        auth_response.user.id = "test-user-id"
        mock_supabase_client.auth.sign_in_with_password = AsyncMock(return_value=auth_response)

        # Mock session creation
        mock_session = MagicMock()
        mock_session_service.create_session = AsyncMock(return_value=mock_session)

        response = await async_client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"
        assert data["token_type"] == "bearer"

        # Verify calls
        mock_supabase_client.auth.sign_in_with_password.assert_called_once()
        mock_session_service.create_session.assert_called_once()
        mock_security_functions['create_access_token'].assert_called_once()
        mock_security_functions['create_refresh_token'].assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client, mock_supabase_client):
        """Test login with invalid credentials."""
        # Mock Supabase auth failure
        mock_supabase_client.auth.sign_in_with_password = AsyncMock(side_effect=Exception("Invalid credentials"))

        response = await async_client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_supabase_error(self, async_client, mock_supabase_client):
        """Test login with Supabase service error."""
        from src.core.errors import ExternalServiceError
        mock_supabase_client.auth.sign_in_with_password = AsyncMock(side_effect=ExternalServiceError("Service unavailable"))

        response = await async_client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "password123"
        })

        assert response.status_code == 503
        data = response.json()
        assert "Authentication service temporarily unavailable" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_session_creation_failure(self, async_client, mock_supabase_client, mock_session_service, mock_security_functions):
        """Test login with session creation failure."""
        # Mock successful Supabase auth
        auth_response = MagicMock()
        auth_response.user = MagicMock()
        auth_response.user.id = "test-user-id"
        mock_supabase_client.auth.sign_in_with_password = AsyncMock(return_value=auth_response)

        # Mock session creation failure
        from src.core.errors import DatabaseError
        mock_session_service.create_session = AsyncMock(side_effect=DatabaseError("Session creation failed"))

        response = await async_client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "password123"
        })

        assert response.status_code == 500
        data = response.json()
        assert "Failed to create user session" in data["detail"]


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, async_client, mock_supabase_client, mock_user_service, mock_security_functions, mock_db):
        """Test successful registration."""
        # Mock Supabase signup
        auth_response = MagicMock()
        auth_response.user = MagicMock()
        auth_response.user.id = "test-user-id"
        mock_supabase_client.auth.sign_up = AsyncMock(return_value=auth_response)

        # Mock user creation
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user_service.create_user_with_id = AsyncMock(return_value=mock_user)

        user_data = UserCreate(
            full_name="Test User",
            email="test@example.com",
            password="password123"
        )

        response = await async_client.post("/auth/register", json=user_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"
        assert data["token_type"] == "bearer"

        # Verify calls
        mock_user_service.create_user_with_id.assert_called_once()
        mock_supabase_client.auth.sign_up.assert_called_once()
        mock_security_functions['create_access_token'].assert_called_once()

    @pytest.mark.asyncio
    async def test_register_supabase_failure_with_rollback(self, async_client, mock_supabase_client, mock_user_service, mock_supabase_admin_client):
        """Test registration with Supabase failure and rollback."""
        # Mock local user creation success
        mock_user = MagicMock()
        mock_user_service.create_user_with_id = AsyncMock(return_value=mock_user)

        # Mock Supabase signup failure
        mock_supabase_client.auth.sign_up = AsyncMock(return_value=MagicMock(user=None))

        # Mock admin client for rollback
        mock_supabase_admin_client.admin.delete_user = AsyncMock()

        user_data = UserCreate(
            full_name="Test User",
            email="test@example.com",
            password="password123"
        )

        response = await async_client.post("/auth/register", json=user_data.model_dump())

        assert response.status_code == 500
        data = response.json()
        assert "Failed to create user account with authentication service" in data["detail"]

        # Verify rollback calls
        mock_user_service.delete_user.assert_called_once()
        mock_supabase_admin_client.admin.delete_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_database_error(self, async_client, mock_user_service):
        """Test registration with database error."""
        from src.core.errors import DatabaseError
        mock_user_service.create_user_with_id = AsyncMock(side_effect=DatabaseError("Database error"))

        user_data = UserCreate(
            full_name="Test User",
            email="test@example.com",
            password="password123"
        )

        response = await async_client.post("/auth/register", json=user_data.model_dump())

        assert response.status_code == 500
        data = response.json()
        assert "Failed to create user account in database" in data["detail"]


class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client, mock_session_service, mock_security_functions, mock_db):
        """Test successful token refresh."""
        # Mock session retrieval
        mock_session = MagicMock()
        mock_session_service.get_session_by_token_hash = AsyncMock(return_value=mock_session)

        # Mock database commit
        mock_db.commit = AsyncMock()

        refresh_request = RefreshTokenRequest(refresh_token="valid_refresh_token")

        response = await async_client.post("/auth/refresh", json=refresh_request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"
        assert data["refresh_token"] == "refresh_token"
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "expires_at" in data

        # Verify calls
        mock_session_service.get_session_by_token_hash.assert_called_once()
        mock_security_functions['verify_refresh_token'].assert_called_once()
        mock_security_functions['create_access_token'].assert_called_once()
        mock_security_functions['create_refresh_token'].assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(self, async_client, mock_security_functions):
        """Test refresh with invalid token."""
        from src.core.errors import AuthenticationError
        mock_security_functions['verify_refresh_token'] = MagicMock(side_effect=AuthenticationError("Invalid token"))

        refresh_request = RefreshTokenRequest(refresh_token="invalid_token")

        response = await async_client.post("/auth/refresh", json=refresh_request.model_dump())

        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired refresh token" in data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_expired_session(self, async_client, mock_session_service, mock_security_functions):
        """Test refresh with expired session."""
        # Mock session not found
        mock_session_service.get_session_by_token_hash = AsyncMock(return_value=None)

        refresh_request = RefreshTokenRequest(refresh_token="expired_token")

        response = await async_client.post("/auth/refresh", json=refresh_request.model_dump())

        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired refresh token" in data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_database_error(self, async_client, mock_session_service, mock_security_functions, mock_db):
        """Test refresh with database error."""
        # Mock session retrieval success
        mock_session = MagicMock()
        mock_session_service.get_session_by_token_hash = AsyncMock(return_value=mock_session)

        # Mock database commit failure
        from src.core.errors import DatabaseError
        mock_db.commit = AsyncMock(side_effect=DatabaseError("Database error"))

        refresh_request = RefreshTokenRequest(refresh_token="valid_token")

        response = await async_client.post("/auth/refresh", json=refresh_request.model_dump())

        assert response.status_code == 500
        data = response.json()
        assert "Failed to refresh token due to database error" in data["detail"]