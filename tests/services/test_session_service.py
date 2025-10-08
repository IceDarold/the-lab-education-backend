import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError

from src.services.session_service import SessionService
from src.models.user_session import UserSession
from src.core.errors import DatabaseError, ValidationError


pytestmark = pytest.mark.asyncio


class TestSessionService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def sample_session(self):
        session = MagicMock(spec=UserSession)
        session.id = uuid4()
        session.user_id = uuid4()
        session.refresh_token_hash = "hashed_token"
        session.device_info = "Chrome"
        session.ip_address = "127.0.0.1"
        session.expires_at = datetime.utcnow() + timedelta(days=7)
        session.is_active = True
        return session

    def test_hash_refresh_token(self):
        # Arrange
        token = "test_refresh_token"

        # Act
        result = SessionService.hash_refresh_token(token)

        # Assert
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length
        # Test deterministic
        assert result == SessionService.hash_refresh_token(token)

    async def test_create_session_success(self, mock_db, sample_session):
        # Arrange
        user_id = uuid4()
        refresh_token = "test_token"
        device_info = "Chrome"
        ip_address = "127.0.0.1"
        expires_delta = timedelta(days=7)

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock the created session
        created_session = MagicMock(spec=UserSession)
        created_session.id = uuid4()
        created_session.user_id = user_id
        created_session.refresh_token_hash = SessionService.hash_refresh_token(refresh_token)
        created_session.device_info = device_info
        created_session.ip_address = ip_address
        created_session.expires_at = datetime.utcnow() + expires_delta
        created_session.is_active = True

        with patch('src.services.session_service.UserSession', return_value=created_session):
            # Act
            result = await SessionService.create_session(
                mock_db, user_id, refresh_token, device_info, ip_address, expires_delta
            )

            # Assert
            assert result == created_session
            assert result.user_id == user_id
            assert result.refresh_token_hash == SessionService.hash_refresh_token(refresh_token)
            assert result.device_info == device_info
            assert result.ip_address == ip_address
            mock_db.add.assert_called_once_with(created_session)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(created_session)

    async def test_create_session_validation_error_empty_token(self, mock_db):
        # Arrange
        user_id = uuid4()
        refresh_token = ""

        # Act & Assert
        with pytest.raises(ValidationError, match="Refresh token is required"):
            await SessionService.create_session(mock_db, user_id, refresh_token)

    async def test_create_session_database_error(self, mock_db):
        # Arrange
        user_id = uuid4()
        refresh_token = "test_token"
        mock_db.add.return_value = None
        mock_db.commit.side_effect = SQLAlchemyError("DB error")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to create session"):
            await SessionService.create_session(mock_db, user_id, refresh_token)
        mock_db.rollback.assert_called_once()

    async def test_get_session_by_token_hash_found_active(self, mock_db, sample_session):
        # Arrange
        token_hash = "hashed_token"
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_session

        with patch('src.services.session_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(hours=1)  # Before expiry

            # Act
            result = await SessionService.get_session_by_token_hash(mock_db, token_hash)

            # Assert
            assert result == sample_session
            mock_db.execute.assert_called_once()

    async def test_get_session_by_token_hash_not_found(self, mock_db):
        # Arrange
        token_hash = "nonexistent_hash"
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Act
        result = await SessionService.get_session_by_token_hash(mock_db, token_hash)

        # Assert
        assert result is None
        mock_db.execute.assert_called_once()

    async def test_get_session_by_token_hash_expired(self, mock_db, sample_session):
        # Arrange
        token_hash = "hashed_token"
        sample_session.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # Query filters out expired

        # Act
        result = await SessionService.get_session_by_token_hash(mock_db, token_hash)

        # Assert
        assert result is None
        mock_db.execute.assert_called_once()

    async def test_get_session_by_token_hash_inactive(self, mock_db, sample_session):
        # Arrange
        token_hash = "hashed_token"
        sample_session.is_active = False
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # Query filters out inactive

        # Act
        result = await SessionService.get_session_by_token_hash(mock_db, token_hash)

        # Assert
        assert result is None
        mock_db.execute.assert_called_once()

    async def test_get_session_by_token_hash_database_error(self, mock_db):
        # Arrange
        token_hash = "hashed_token"
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to lookup session"):
            await SessionService.get_session_by_token_hash(mock_db, token_hash)

    async def test_invalidate_session_success(self, mock_db):
        # Arrange
        session_id = uuid4()
        mock_db.execute.return_value.rowcount = 1

        # Act
        result = await SessionService.invalidate_session(mock_db, session_id)

        # Assert
        assert result is True
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_invalidate_session_not_found(self, mock_db):
        # Arrange
        session_id = uuid4()
        mock_db.execute.return_value.rowcount = 0

        # Act
        result = await SessionService.invalidate_session(mock_db, session_id)

        # Assert
        assert result is False
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_invalidate_session_database_error(self, mock_db):
        # Arrange
        session_id = uuid4()
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to invalidate session"):
            await SessionService.invalidate_session(mock_db, session_id)
        mock_db.rollback.assert_called_once()

    async def test_invalidate_user_sessions_success(self, mock_db):
        # Arrange
        user_id = uuid4()
        mock_db.execute.return_value.rowcount = 3

        # Act
        result = await SessionService.invalidate_user_sessions(mock_db, user_id)

        # Assert
        assert result == 3
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_invalidate_user_sessions_database_error(self, mock_db):
        # Arrange
        user_id = uuid4()
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to invalidate user sessions"):
            await SessionService.invalidate_user_sessions(mock_db, user_id)
        mock_db.rollback.assert_called_once()

    async def test_cleanup_expired_sessions_success(self, mock_db):
        # Arrange
        mock_db.execute.return_value.rowcount = 5

        # Act
        result = await SessionService.cleanup_expired_sessions(mock_db)

        # Assert
        assert result == 5
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_cleanup_expired_sessions_database_error(self, mock_db):
        # Arrange
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to cleanup expired sessions"):
            await SessionService.cleanup_expired_sessions(mock_db)
        mock_db.rollback.assert_called_once()