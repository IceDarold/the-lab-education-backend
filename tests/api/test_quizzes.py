import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

from src.main import app
from src.schemas.user import User
from src.core.security import get_current_user
from src.api.v1.quizzes import get_answers_table


@pytest.fixture
def mock_current_user():
    """Mock current user."""
    return User(
        user_id=uuid4(),
        full_name="Test User",
        email="test@example.com",
        role="student"
    )


@pytest.fixture
def override_current_user(mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_answers_table():
    """Override the answers table dependency."""
    answers_table = MagicMock()
    app.dependency_overrides[get_answers_table] = lambda: answers_table
    yield answers_table
    app.dependency_overrides.pop(get_answers_table, None)


@pytest.mark.asyncio
async def test_check_quiz_answer_correct(mock_current_user, override_answers_table, override_current_user):
    """Test successful quiz answer check with correct answer."""
    answers_table = override_answers_table
    correct_answer_id = str(uuid4())
    question_id = str(uuid4())
    selected_answer_id = correct_answer_id

    # Mock the query chain
    response_mock = MagicMock()
    response_mock.data = {"correct_answer_id": correct_answer_id}
    query_mock = MagicMock()
    query_mock.execute = AsyncMock(return_value=response_mock)
    answers_table.eq.return_value.single.return_value = query_mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["correct_answer_id"] == correct_answer_id


@pytest.mark.asyncio
async def test_check_quiz_answer_incorrect(mock_current_user, override_answers_table, override_current_user):
    """Test quiz answer check with incorrect answer."""
    answers_table = override_answers_table
    correct_answer_id = str(uuid4())
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())  # Different from correct

    # Mock the query chain
    response_mock = MagicMock()
    response_mock.data = {"correct_answer_id": correct_answer_id}
    query_mock = MagicMock()
    query_mock.execute = AsyncMock(return_value=response_mock)
    answers_table.eq.return_value.single.return_value = query_mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False
    assert data["correct_answer_id"] == correct_answer_id


@pytest.mark.asyncio
async def test_check_quiz_answer_question_not_found(mock_current_user, override_answers_table, override_current_user):
    """Test quiz answer check when question is not found."""
    answers_table = override_answers_table
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())

    # Mock the query chain to raise exception
    query_mock = MagicMock()
    query_mock.execute = AsyncMock(side_effect=Exception("Query failed"))
    answers_table.eq.return_value.single.return_value = query_mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Question not found" in data["detail"]


@pytest.mark.asyncio
async def test_check_quiz_answer_database_exception(mock_current_user, override_answers_table, override_current_user):
    """Test quiz answer check with database query exception."""
    answers_table = override_answers_table
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())

    # Mock the query chain to raise exception
    query_mock = MagicMock()
    query_mock.execute = AsyncMock(side_effect=Exception("Database error"))
    answers_table.eq.return_value.single.return_value = query_mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Question not found" in data["detail"]


@pytest.mark.asyncio
async def test_check_quiz_answer_missing_correct_answer_id(mock_current_user, override_answers_table, override_current_user):
    """Test quiz answer check when correct_answer_id is missing."""
    answers_table = override_answers_table
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())

    # Mock the query chain
    response_mock = MagicMock()
    response_mock.data = {}  # No correct_answer_id
    query_mock = MagicMock()
    query_mock.execute = AsyncMock(return_value=response_mock)
    answers_table.eq.return_value.single.return_value = query_mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Question not found" in data["detail"]
