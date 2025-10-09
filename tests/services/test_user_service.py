import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError
from src.services.user_service import UserService, UserNotFoundException, IncorrectPasswordException
from src.models.user import User
from src.schemas.user import UserCreate
from src.schemas import UserFilter


pytestmark = pytest.mark.asyncio


class TestUserService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def sample_user(self):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.hashed_password = UserService.hash_password("password123")
        user.role = "STUDENT"
        user.status = "ACTIVE"
        return user

    async def test_get_user_by_email_found(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_user

        # Act
        result = await UserService.get_user_by_email("test@example.com", mock_db)

        # Assert
        assert result == sample_user
        mock_db.execute.assert_called_once()

    async def test_get_user_by_email_not_found(self, mock_db):
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Act
        result = await UserService.get_user_by_email("nonexistent@example.com", mock_db)

        # Assert
        assert result is None
        mock_db.execute.assert_called_once()

    async def test_create_user_success(self, mock_db, sample_user):
        # Arrange
        user_data = UserCreate(full_name="Test User", email="test@example.com", password="password123")
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock the created user
        created_user = MagicMock(spec=User)
        created_user.id = 1
        created_user.email = "test@example.com"
        created_user.full_name = "Test User"
        created_user.hashed_password = "hashed_password"
        created_user.role = "STUDENT"
        created_user.status = "ACTIVE"

        # Act
        result = await UserService.create_user(user_data, mock_db)

        # Assert
        assert result.full_name == "Test User"
        assert result.email == "test@example.com"
        assert result.hashed_password != "password123"  # Should be hashed
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_create_user_integrity_error(self, mock_db):
        # Arrange
        user_data = UserCreate(full_name="Test User", email="test@example.com", password="password123")
        mock_db.add.return_value = None
        mock_db.commit.side_effect = IntegrityError(None, None, None)

        # Act & Assert
        with pytest.raises(IntegrityError):
            await UserService.create_user(user_data, mock_db)

    async def test_authenticate_user_success(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_user

        # Act
        result = await UserService.authenticate_user("test@example.com", "password123", mock_db)

        # Assert
        assert result == sample_user

    async def test_authenticate_user_user_not_found(self, mock_db):
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Act
        result = await UserService.authenticate_user("nonexistent@example.com", "password123", mock_db)

        # Assert
        assert result is None

    async def test_authenticate_user_wrong_password(self, mock_db, sample_user):
        # Arrange
        sample_user.hashed_password = "different_hash"
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_user

        # Act
        result = await UserService.authenticate_user("test@example.com", "wrongpassword", mock_db)

        # Assert
        assert result is None

    async def test_list_users_no_filters(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter())

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user
        mock_db.execute.assert_called_once()

    async def test_list_users_with_search(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter(search="Test"))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    async def test_list_users_with_role_filter(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter(role="STUDENT"))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    async def test_list_users_with_status_filter(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter(status="ACTIVE"))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    async def test_list_users_with_sorting_desc(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter(sort_by="email", sort_order="desc"))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    async def test_list_users_with_sorting_asc(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter(sort_by="full_name", sort_order="asc"))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    async def test_list_users_with_pagination(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter(skip=10, limit=5))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    async def test_list_users_empty_result(self, mock_db):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        # Act
        result = await UserService.list_users(mock_db, UserFilter())

        # Assert
        assert result == []

    async def test_list_users_invalid_sort_by(self, mock_db, sample_user):
        # Arrange
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_user]

        # Act
        result = await UserService.list_users(mock_db, UserFilter(sort_by="invalid_field"))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user
