import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock
from httpx import ASGITransport, AsyncClient
from tests.utils import assert_success_response, assert_created, create_test_user
from src.main import app
from src.core.security import get_current_user
from src.schemas.user import User


@pytest.mark.integration
async def test_enroll_in_course_success(monkeypatch):
    test_user = User(user_id=UUID("11111111-1111-1111-1111-111111111111"), full_name="Test", email="user@example.com")

    async def mock_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    client_mock = MagicMock()

    course_query = MagicMock()
    course_query.select.return_value = course_query
    course_query.eq.return_value = course_query
    course_query.single.return_value = course_query
    course_id = "22222222-2222-2222-2222-222222222222"
    course_query.execute = AsyncMock(return_value=MagicMock(data={"id": course_id}))

    enrollments_table = MagicMock()
    insert_call = MagicMock()
    insert_call.execute = AsyncMock(return_value=MagicMock())
    enrollments_table.insert.return_value = insert_call

    def table_side_effect(name: str):
        if name == "courses":
            return course_query
        if name == "enrollments":
            return enrollments_table
        raise AssertionError("Unexpected table name")

    client_mock.table.side_effect = table_side_effect

    patched = False
    for module_path in ["src.api.v1.courses", "src.db.session"]:
        try:
            monkeypatch.setattr(f"{module_path}.get_supabase_client", lambda: client_mock)
            patched = True
        except AttributeError:
            continue

    if not patched:
        raise AssertionError("Could not patch get_supabase_client")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            response = await async_client.post(
                "/api/v1/courses/test-course/enroll",
                headers={"Authorization": "Bearer token"},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
    enrollments_table.insert.assert_called_once_with(
        {
            "user_id": str(test_user.user_id),
            "course_id": course_id,
        }
    )
    insert_call.execute.assert_awaited()


@pytest.mark.integration
async def test_get_my_courses(monkeypatch):
    test_user = User(user_id=UUID("11111111-1111-1111-1111-111111111111"), full_name="Test", email="user@example.com")

    async def mock_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    client_mock = MagicMock()
    rpc_course_id = "33333333-3333-3333-3333-333333333333"
    rpc_response = MagicMock(
        data=[
            {
                "course_id": rpc_course_id,
                "slug": "test-course",
                "title": "Test Course",
                "progress_percent": 75,
            }
        ]
    )
    client_mock.rpc = AsyncMock(return_value=rpc_response)

    patched = False
    for module_path in ["src.api.v1.dashboard", "src.db.session"]:
        try:
            monkeypatch.setattr(f"{module_path}.get_supabase_client", lambda: client_mock)
            patched = True
        except AttributeError:
            continue

    if not patched:
        raise AssertionError("Could not patch get_supabase_client")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            response = await async_client.get(
                "/api/v1/dashboard/my-courses",
                headers={"Authorization": "Bearer token"},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data[0]["progress_percent"] == 75
    client_mock.rpc.assert_awaited_once_with(
        "get_my_courses_with_progress",
        {"user_id": str(test_user.user_id)},
    )


@pytest.mark.integration
async def test_get_course_details_with_progress(monkeypatch):
    test_user = User(user_id=UUID("11111111-1111-1111-1111-111111111111"), full_name="Test", email="user@example.com")

    async def mock_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    client_mock = MagicMock()
    lesson_uuid = "44444444-4444-4444-4444-444444444444"
    rpc_response = MagicMock(
        data={
            "title": "Course",
            "overall_progress_percent": 80,
            "modules": [
                {
                    "title": "Module 1",
                    "lessons": [
                        {
                            "title": "Lesson 1",
                            "lesson_id": lesson_uuid,
                            "slug": "lesson-1",
                            "status": "completed",
                        }
                    ],
                }
            ],
        }
    )
    client_mock.rpc = AsyncMock(return_value=rpc_response)

    patched = False
    for module_path in ["src.api.v1.dashboard", "src.db.session"]:
        try:
            monkeypatch.setattr(f"{module_path}.get_supabase_client", lambda: client_mock)
            patched = True
        except AttributeError:
            continue

    if not patched:
        raise AssertionError("Could not patch get_supabase_client")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            response = await async_client.get(
                "/api/v1/dashboard/courses/test-course",
                headers={"Authorization": "Bearer token"},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["modules"][0]["lessons"][0]["status"] == "completed"
    client_mock.rpc.assert_awaited_once_with(
        "get_course_details_for_user",
        {"user_id": str(test_user.user_id), "course_slug": "test-course"},
    )


@pytest.mark.integration
async def test_get_my_courses_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.get("/api/v1/dashboard/my-courses")

    assert response.status_code == 401
