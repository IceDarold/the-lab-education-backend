import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from jwt import ExpiredSignatureError, PyJWTError

from src.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    get_current_admin,
)
from src.schemas.user import User


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("src.core.security.settings") as mock_settings:
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        yield mock_settings


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "sub": str(uuid4()),
        "email": "test@example.com",
    }


@pytest.fixture
def sample_user():
    """Sample User object for testing."""
    return User(
        user_id=uuid4(),
        full_name="Test User",
        email="test@example.com",
        role="student",
    )


@pytest.fixture
def admin_user():
    """Sample admin User object for testing."""
    return User(
        user_id=uuid4(),
        full_name="Admin User",
        email="admin@example.com",
        role="admin",
    )


class TestCreateAccessToken:
    def test_create_access_token_default_expiration(self, mock_settings, sample_user_data):
        """Test creating access token with default expiration."""
        token = create_access_token(sample_user_data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_custom_expiration(self, mock_settings, sample_user_data):
        """Test creating access token with custom expiration."""
        custom_expires = timedelta(minutes=30)
        token = create_access_token(sample_user_data, expires_delta=custom_expires)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_payload_encoding(self, mock_settings, sample_user_data):
        """Test that access token encodes payload correctly."""
        with patch("jwt.encode") as mock_encode:
            mock_encode.return_value = "mocked-token"
            token = create_access_token(sample_user_data)

            # Check that encode was called with correct data
            call_args = mock_encode.call_args[0][0]  # First positional argument
            assert call_args["sub"] == sample_user_data["sub"]
            assert call_args["email"] == sample_user_data["email"]
            assert call_args["type"] == "access"
            assert "exp" in call_args
            assert isinstance(call_args["exp"], datetime)


class TestCreateRefreshToken:
    def test_create_refresh_token_default_expiration(self, mock_settings, sample_user_data):
        """Test creating refresh token with default expiration."""
        token = create_refresh_token(sample_user_data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_custom_expiration(self, mock_settings, sample_user_data):
        """Test creating refresh token with custom expiration."""
        custom_expires = timedelta(days=14)
        token = create_refresh_token(sample_user_data, expires_delta=custom_expires)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_payload_encoding(self, mock_settings, sample_user_data):
        """Test that refresh token encodes payload correctly."""
        with patch("jwt.encode") as mock_encode:
            mock_encode.return_value = "mocked-token"
            token = create_refresh_token(sample_user_data)

            # Check that encode was called with correct data
            call_args = mock_encode.call_args[0][0]
            assert call_args["sub"] == sample_user_data["sub"]
            assert call_args["email"] == sample_user_data["email"]
            assert call_args["type"] == "refresh"
            assert "exp" in call_args
            assert isinstance(call_args["exp"], datetime)


class TestVerifyRefreshToken:
    def test_verify_refresh_token_valid(self, mock_settings, sample_user_data):
        """Test verifying a valid refresh token."""
        sample_user_data["type"] = "refresh"
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = sample_user_data
            payload = verify_refresh_token("valid-token")

            assert payload == sample_user_data
            mock_decode.assert_called_once_with(
                "valid-token",
                mock_settings.SECRET_KEY,
                algorithms=[mock_settings.ALGORITHM]
            )

    def test_verify_refresh_token_expired(self, mock_settings):
        """Test verifying an expired refresh token."""
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = ExpiredSignatureError("Token expired")

            with pytest.raises(HTTPException) as exc_info:
                verify_refresh_token("expired-token")

            assert exc_info.value.status_code == 401
            assert "Refresh token expired" in exc_info.value.detail

    def test_verify_refresh_token_invalid(self, mock_settings):
        """Test verifying an invalid refresh token."""
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = PyJWTError("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                verify_refresh_token("invalid-token")

            assert exc_info.value.status_code == 401
            assert "Invalid refresh token" in exc_info.value.detail

    def test_verify_refresh_token_wrong_type(self, mock_settings, sample_user_data):
        """Test verifying a token with wrong type."""
        sample_user_data["type"] = "access"  # Wrong type for refresh token
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = sample_user_data

            with pytest.raises(HTTPException) as exc_info:
                verify_refresh_token("wrong-type-token")

            assert exc_info.value.status_code == 401
            assert "Invalid token type" in exc_info.value.detail


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_valid(self, mock_settings, sample_user_data, sample_user):
        """Test getting current user with valid access token."""
        sample_user_data["type"] = "access"
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = sample_user_data

            user = await get_current_user("valid-token")

            assert isinstance(user, User)
            assert user.user_id == sample_user_data["sub"]
            assert user.email == sample_user_data["email"]
            assert user.role == "student"  # Default role

    @pytest.mark.asyncio
    async def test_get_current_user_expired(self, mock_settings):
        """Test getting current user with expired token."""
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = ExpiredSignatureError("Token expired")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("expired-token")

            assert exc_info.value.status_code == 401
            assert "Token expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid(self, mock_settings):
        """Test getting current user with invalid token."""
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = JWTError("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("invalid-token")

            assert exc_info.value.status_code == 401
            assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_wrong_type(self, mock_settings, sample_user_data):
        """Test getting current user with wrong token type."""
        sample_user_data["type"] = "refresh"  # Wrong type for access
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = sample_user_data

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("wrong-type-token")

            assert exc_info.value.status_code == 401
            assert "Invalid token type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_payload(self, mock_settings):
        """Test getting current user with missing payload data."""
        incomplete_payload = {"type": "access"}  # Missing sub and email
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = incomplete_payload

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("incomplete-token")

            assert exc_info.value.status_code == 401
            assert "Invalid token payload" in exc_info.value.detail


class TestGetCurrentAdmin:
    @pytest.mark.asyncio
    async def test_get_current_admin_admin_user(self, admin_user):
        """Test getting current admin with admin user."""
        result = await get_current_admin(admin_user)

        assert result == admin_user
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_get_current_admin_non_admin_user(self, sample_user):
        """Test getting current admin with non-admin user."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin(sample_user)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail