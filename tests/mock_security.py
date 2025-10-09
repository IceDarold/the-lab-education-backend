"""
Test security utilities that bypass authentication for testing.
"""
from src.schemas.user import User
from uuid import uuid4


# Test users for different roles
TEST_USER = User(
    user_id=uuid4(),
    full_name="Test User",
    email="test@example.com",
    role="student"
)

TEST_ADMIN = User(
    user_id=uuid4(),
    full_name="Test Admin",
    email="admin@example.com",
    role="admin"
)


async def get_current_user() -> User:
    """Test version that returns a mock user without authentication."""
    return TEST_USER


async def get_current_admin() -> User:
    """Test version that returns a mock admin without authentication."""
    return TEST_ADMIN


def create_access_token(data: dict) -> str:
    """Test version that returns a dummy token."""
    return "test_access_token"


def create_refresh_token(data: dict) -> str:
    """Test version that returns a dummy token."""
    return "test_refresh_token"


def verify_refresh_token(token: str) -> dict:
    """Test version that returns dummy payload."""
    return {
        "sub": str(TEST_USER.user_id),
        "email": TEST_USER.email,
        "type": "refresh"
    }