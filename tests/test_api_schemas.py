import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4
from src.schemas.api import CreateCourseRequest, CreateModuleRequest, CreateLessonRequest
from src.schemas import UserCreate, UserUpdate, UserResponse, LessonCompleteRequest, UsersListResponse, UserFilter, DailyActivity, ActivityDetailsResponse
from src.schemas.user import User, CheckEmailRequest, ForgotPasswordRequest, ResetPasswordRequest
from src.schemas.content_node import ContentNode
from src.schemas.course import CoursePublic
from src.schemas.lesson import LessonContent, LessonCompleteResponse
from src.schemas.quiz import QuizCheckRequest, QuizCheckResponse
from src.schemas.token import RefreshTokenRequest, RefreshTokenResponse


@pytest.mark.unit
class TestCreateCourseRequest:
    def test_valid_creation(self):
        """Test successful creation with valid data."""
        request = CreateCourseRequest(title="Machine Learning", slug="ml-course")
        assert request.title == "Machine Learning"
        assert request.slug == "ml-course"

    def test_missing_title(self):
        """Test validation error when title is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCourseRequest(slug="ml-course")
        assert "title" in str(exc_info.value)

    def test_missing_slug(self):
        """Test validation error when slug is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCourseRequest(title="Machine Learning")
        assert "slug" in str(exc_info.value)

    def test_empty_title(self):
        """Test validation error when title is empty."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCourseRequest(title="", slug="ml-course")
        assert "title" in str(exc_info.value)

    def test_empty_slug(self):
        """Test validation error when slug is empty."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCourseRequest(title="Machine Learning", slug="")
        assert "slug" in str(exc_info.value)


@pytest.mark.unit
class TestCreateModuleRequest:
    def test_valid_creation(self):
        """Test successful creation with valid data."""
        request = CreateModuleRequest(title="Supervised Learning", slug="supervised", parent_slug="ml-course")
        assert request.title == "Supervised Learning"
        assert request.slug == "supervised"
        assert request.parent_slug == "ml-course"

    def test_missing_title(self):
        """Test validation error when title is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateModuleRequest(slug="supervised", parent_slug="ml-course")
        assert "title" in str(exc_info.value)

    def test_missing_slug(self):
        """Test validation error when slug is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateModuleRequest(title="Supervised Learning", parent_slug="ml-course")
        assert "slug" in str(exc_info.value)

    def test_missing_parent_slug(self):
        """Test validation error when parent_slug is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateModuleRequest(title="Supervised Learning", slug="supervised")
        assert "parent_slug" in str(exc_info.value)

    def test_empty_fields(self):
        """Test validation errors when fields are empty."""
        with pytest.raises(ValidationError) as exc_info:
            CreateModuleRequest(title="", slug="", parent_slug="")
        errors = exc_info.value.errors()
        assert len(errors) == 3
        fields = {error["loc"][0] for error in errors}
        assert fields == {"title", "slug", "parent_slug"}


@pytest.mark.unit
class TestCreateLessonRequest:
    def test_valid_creation(self):
        """Test successful creation with valid data."""
        request = CreateLessonRequest(title="What is ML?", slug="what-is-ml", parent_slug="ml-foundations")
        assert request.title == "What is ML?"
        assert request.slug == "what-is-ml"
        assert request.parent_slug == "ml-foundations"

    def test_missing_title(self):
        """Test validation error when title is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateLessonRequest(slug="what-is-ml", parent_slug="ml-foundations")
        assert "title" in str(exc_info.value)

    def test_missing_slug(self):
        """Test validation error when slug is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateLessonRequest(title="What is ML?", parent_slug="ml-foundations")
        assert "slug" in str(exc_info.value)

    def test_missing_parent_slug(self):
        """Test validation error when parent_slug is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateLessonRequest(title="What is ML?", slug="what-is-ml")
        assert "parent_slug" in str(exc_info.value)

    def test_empty_fields(self):
        """Test validation errors when fields are empty."""
        with pytest.raises(ValidationError) as exc_info:
            CreateLessonRequest(title="", slug="", parent_slug="")
        errors = exc_info.value.errors()
        assert len(errors) == 3
        fields = {error["loc"][0] for error in errors}
        assert fields == {"title", "slug", "parent_slug"}


@pytest.mark.unit
class TestUserCreate:
    def test_valid_creation(self):
        """Test successful creation with valid data."""
        user = UserCreate(full_name="John Doe", email="john@example.com", password="password123")
        assert user.full_name == "John Doe"
        assert user.email == "john@example.com"
        assert user.password == "password123"

    def test_missing_full_name(self):
        """Test validation error when full_name is missing."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="john@example.com", password="password123")
        assert "full_name" in str(exc_info.value)

    def test_missing_email(self):
        """Test validation error when email is missing."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="John Doe", password="password123")
        assert "email" in str(exc_info.value)

    def test_missing_password(self):
        """Test validation error when password is missing."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="John Doe", email="john@example.com")
        assert "password" in str(exc_info.value)

    def test_empty_full_name(self):
        """Test validation error when full_name is empty."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="", email="john@example.com", password="password123")
        assert "full_name" in str(exc_info.value)

    def test_full_name_too_long(self):
        """Test validation error when full_name is too long."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="a" * 101, email="john@example.com", password="password123")
        assert "full_name" in str(exc_info.value)

    def test_email_too_long(self):
        """Test validation error when email is too long."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="John Doe", email="a" * 255 + "@example.com", password="password123")
        assert "email" in str(exc_info.value)

    def test_password_too_short(self):
        """Test validation error when password is too short."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="John Doe", email="john@example.com", password="1234567")
        assert "password" in str(exc_info.value)

    def test_password_too_long(self):
        """Test validation error when password is too long."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="John Doe", email="john@example.com", password="a" * 129)
        assert "password" in str(exc_info.value)

    def test_invalid_email(self):
        """Test validation error when email is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(full_name="John Doe", email="invalid-email", password="password123")
        assert "email" in str(exc_info.value)


@pytest.mark.unit
class TestUserUpdate:
    def test_valid_update_all_fields(self):
        """Test successful update with all fields."""
        update = UserUpdate(full_name="Jane Doe", email="jane@example.com", role="admin")
        assert update.full_name == "Jane Doe"
        assert update.email == "jane@example.com"
        assert update.role == "admin"

    def test_valid_update_partial_fields(self):
        """Test successful update with partial fields."""
        update = UserUpdate(full_name="Jane Doe")
        assert update.full_name == "Jane Doe"
        assert update.email is None
        assert update.role is None
        assert update.status is None

    def test_valid_update_no_fields(self):
        """Test successful update with no fields."""
        update = UserUpdate()
        assert update.full_name is None
        assert update.email is None
        assert update.role is None
        assert update.status is None

    def test_full_name_too_long(self):
        """Test validation error when full_name is too long."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(full_name="a" * 101)
        assert "full_name" in str(exc_info.value)

    def test_email_too_long(self):
        """Test validation error when email is too long."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(email="a" * 255 + "@example.com")
        assert "email" in str(exc_info.value)


@pytest.mark.unit
class TestUserResponse:
    def test_valid_response(self):
        """Test successful serialization."""
        response = UserResponse(
            id=1,
            full_name="John Doe",
            email="john@example.com",
            role="student",
            status="active",
            registration_date=datetime(2023, 1, 1, 12, 0, 0)
        )
        assert response.id == 1
        assert response.full_name == "John Doe"
        assert response.email == "john@example.com"
        assert response.role == "student"
        assert response.status == "active"
        assert response.registration_date == datetime(2023, 1, 1, 12, 0, 0)

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            UserResponse(
                id=1,
                email="john@example.com",
                role="student",
                status="active",
                registration_date=datetime(2023, 1, 1, 12, 0, 0)
            )
        assert "full_name" in str(exc_info.value)


@pytest.mark.unit
class TestLessonCompleteRequest:
    def test_valid_request(self):
        """Test successful creation with valid course_slug."""
        request = LessonCompleteRequest(course_slug="ml-course")
        assert request.course_slug == "ml-course"

    def test_missing_course_slug(self):
        """Test validation error when course_slug is missing."""
        with pytest.raises(ValidationError) as exc_info:
            LessonCompleteRequest()
        assert "course_slug" in str(exc_info.value)

    def test_empty_course_slug(self):
        """Test validation error when course_slug is empty."""
        with pytest.raises(ValidationError) as exc_info:
            LessonCompleteRequest(course_slug="")
        assert "course_slug" in str(exc_info.value)

    def test_invalid_course_slug(self):
        """Test validation error when course_slug contains invalid characters."""
        with pytest.raises(ValidationError) as exc_info:
            LessonCompleteRequest(course_slug="ml course")
        assert "course_slug" in str(exc_info.value)


@pytest.mark.unit
class TestUsersListResponse:
    def test_valid_response(self):
        """Test successful creation with valid pagination fields."""
        user = UserResponse(
            id=1,
            full_name="John Doe",
            email="john@example.com",
            role="student",
            status="active",
            registration_date=datetime(2023, 1, 1, 12, 0, 0)
        )
        response = UsersListResponse(
            users=[user],
            total_items=1,
            total_pages=1,
            current_page=1,
            page_size=10
        )
        assert len(response.users) == 1
        assert response.total_items == 1
        assert response.total_pages == 1
        assert response.current_page == 1
        assert response.page_size == 10

    def test_empty_users_list(self):
        """Test response with empty users list."""
        response = UsersListResponse(
            users=[],
            total_items=0,
            total_pages=0,
            current_page=1,
            page_size=10
        )
        assert len(response.users) == 0
        assert response.total_items == 0


@pytest.mark.unit
class TestUserFilter:
    def test_valid_filter_all_fields(self):
        """Test successful creation with all filter fields."""
        filter_obj = UserFilter(
            search="john",
            role="student",
            status="active",
            sort_by="id",
            sort_order="asc",
            skip=0,
            limit=10
        )
        assert filter_obj.search == "john"
        assert filter_obj.role == "student"
        assert filter_obj.status == "active"
        assert filter_obj.sort_by == "id"
        assert filter_obj.sort_order == "asc"
        assert filter_obj.skip == 0
        assert filter_obj.limit == 10

    def test_valid_filter_defaults(self):
        """Test filter with default values."""
        filter_obj = UserFilter()
        assert filter_obj.search is None
        assert filter_obj.role is None
        assert filter_obj.status is None
        assert filter_obj.sort_by == "registration_date"
        assert filter_obj.sort_order == "desc"
        assert filter_obj.skip == 0
        assert filter_obj.limit == 100

    def test_search_too_long(self):
        """Test validation error when search is too long."""
        with pytest.raises(ValidationError) as exc_info:
            UserFilter(search="a" * 101)
        assert "search" in str(exc_info.value)


@pytest.mark.unit
class TestDailyActivity:
    def test_valid_activity(self):
        """Test successful creation with valid data."""
        activity = DailyActivity(
            date="2023-01-01",
            LOGIN=5,
            LESSON_COMPLETED=2,
            QUIZ_ATTEMPT=1,
            CODE_EXECUTION=3
        )
        assert activity.date == "2023-01-01"
        assert activity.LOGIN == 5
        assert activity.LESSON_COMPLETED == 2
        assert activity.QUIZ_ATTEMPT == 1
        assert activity.CODE_EXECUTION == 3

    def test_activity_with_none_values(self):
        """Test activity with some None values."""
        activity = DailyActivity(date="2023-01-01", LOGIN=5)
        assert activity.date == "2023-01-01"
        assert activity.LOGIN == 5
        assert activity.LESSON_COMPLETED is None

    def test_missing_date(self):
        """Test validation error when date is missing."""
        with pytest.raises(ValidationError) as exc_info:
            DailyActivity(LOGIN=5)
        assert "date" in str(exc_info.value)


@pytest.mark.unit
class TestActivityDetailsResponse:
    def test_valid_response(self):
        """Test successful creation with activity list."""
        activity = DailyActivity(date="2023-01-01", LOGIN=5)
        response = ActivityDetailsResponse(activities=[activity])
        assert len(response.activities) == 1
        assert response.activities[0].date == "2023-01-01"

    def test_empty_activities(self):
        """Test response with empty activities list."""
        response = ActivityDetailsResponse(activities=[])
        assert len(response.activities) == 0


@pytest.mark.unit
class TestContentNode:
    def test_valid_node(self):
        """Test successful creation of ContentNode."""
        node = ContentNode(type="course", name="ML Course", path="/courses/ml")
        assert node.type == "course"
        assert node.name == "ML Course"
        assert node.path == "/courses/ml"
        assert node.children == []

    def test_node_with_children(self):
        """Test node with children."""
        child = ContentNode(type="module", name="Basics", path="/courses/ml/basics")
        node = ContentNode(type="course", name="ML Course", path="/courses/ml", children=[child])
        assert len(node.children) == 1
        assert node.children[0].name == "Basics"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            ContentNode(type="course", path="/courses/ml")
        assert "name" in str(exc_info.value)


@pytest.mark.unit
class TestCoursePublic:
    def test_valid_course(self):
        """Test successful creation of CoursePublic."""
        course = CoursePublic(
            course_id=uuid4(),
            slug="ml-course",
            title="Machine Learning",
            summary="Learn ML",
            description="Comprehensive ML course",
            cover_image_url="https://example.com/image.jpg"
        )
        assert course.slug == "ml-course"
        assert course.title == "Machine Learning"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            CoursePublic(
                course_id=uuid4(),
                title="Machine Learning",
                summary="Learn ML"
            )
        assert "slug" in str(exc_info.value)

    def test_invalid_slug(self):
        """Test validation error when slug is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CoursePublic(
                course_id=uuid4(),
                slug="ml course",
                title="Machine Learning"
            )
        assert "slug" in str(exc_info.value)


@pytest.mark.unit
class TestLessonContent:
    def test_valid_lesson(self):
        """Test successful creation of LessonContent."""
        lesson = LessonContent(
            slug="intro",
            title="Introduction",
            course_slug="ml-course",
            lesson_id=uuid4(),
            metadata={"key": "value"},
            cells=[]
        )
        assert lesson.slug == "intro"
        assert lesson.title == "Introduction"
        assert lesson.course_slug == "ml-course"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            LessonContent(title="Introduction")
        assert "slug" in str(exc_info.value)

    def test_invalid_slug(self):
        """Test validation error when slug is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            LessonContent(slug="intro lesson", title="Introduction")
        assert "slug" in str(exc_info.value)


@pytest.mark.unit
class TestQuizCheckRequest:
    def test_valid_request(self):
        """Test successful creation of QuizCheckRequest."""
        request = QuizCheckRequest(
            question_id=uuid4(),
            selected_answer_id=uuid4()
        )
        assert isinstance(request.question_id, UUID)
        assert isinstance(request.selected_answer_id, UUID)

    def test_missing_fields(self):
        """Test validation error when fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            QuizCheckRequest(question_id=uuid4())
        assert "selected_answer_id" in str(exc_info.value)


@pytest.mark.unit
class TestQuizCheckResponse:
    def test_valid_response(self):
        """Test successful creation of QuizCheckResponse."""
        response = QuizCheckResponse(
            is_correct=True,
            correct_answer_id=uuid4()
        )
        assert response.is_correct is True
        assert isinstance(response.correct_answer_id, UUID)

    def test_missing_fields(self):
        """Test validation error when fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            QuizCheckResponse(is_correct=True)
        assert "correct_answer_id" in str(exc_info.value)


@pytest.mark.unit
class TestRefreshTokenRequest:
    def test_valid_request(self):
        """Test successful creation of RefreshTokenRequest."""
        request = RefreshTokenRequest(refresh_token="token123")
        assert request.refresh_token == "token123"

    def test_missing_token(self):
        """Test validation error when refresh_token is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RefreshTokenRequest()
        assert "refresh_token" in str(exc_info.value)


@pytest.mark.unit
class TestRefreshTokenResponse:
    def test_valid_response(self):
        """Test successful creation of RefreshTokenResponse."""
        response = RefreshTokenResponse(
            access_token="access123",
            refresh_token="refresh123",
            token_type="bearer",
            expires_in=3600,
            expires_at=1234567890
        )
        assert response.access_token == "access123"
        assert response.refresh_token == "refresh123"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
        assert response.expires_at == 1234567890

    def test_minimal_response(self):
        """Test response with minimal fields."""
        response = RefreshTokenResponse(access_token="access123")
        assert response.access_token == "access123"
        assert response.refresh_token is None
        assert response.token_type == "bearer"


@pytest.mark.unit
class TestUser:
    def test_valid_user(self):
        """Test successful creation of User."""
        user = User(
            user_id=uuid4(),
            full_name="John Doe",
            email="john@example.com",
            role="student"
        )
        assert user.full_name == "John Doe"
        assert user.email == "john@example.com"
        assert user.role == "student"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                user_id=uuid4(),
                email="john@example.com",
                role="student"
            )
        assert "full_name" in str(exc_info.value)

    def test_invalid_email(self):
        """Test validation error when email is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                user_id=uuid4(),
                full_name="John Doe",
                email="invalid-email",
                role="student"
            )
        assert "email" in str(exc_info.value)


@pytest.mark.unit
class TestCheckEmailRequest:
    def test_valid_request(self):
        """Test successful creation of CheckEmailRequest."""
        request = CheckEmailRequest(email="john@example.com")
        assert request.email == "john@example.com"

    def test_missing_email(self):
        """Test validation error when email is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CheckEmailRequest()
        assert "email" in str(exc_info.value)

    def test_invalid_email(self):
        """Test validation error when email is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CheckEmailRequest(email="invalid-email")
        assert "email" in str(exc_info.value)


@pytest.mark.unit
class TestForgotPasswordRequest:
    def test_valid_request(self):
        """Test successful creation of ForgotPasswordRequest."""
        request = ForgotPasswordRequest(email="john@example.com")
        assert request.email == "john@example.com"

    def test_missing_email(self):
        """Test validation error when email is missing."""
        with pytest.raises(ValidationError) as exc_info:
            ForgotPasswordRequest()
        assert "email" in str(exc_info.value)

    def test_invalid_email(self):
        """Test validation error when email is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ForgotPasswordRequest(email="invalid-email")
        assert "email" in str(exc_info.value)


@pytest.mark.unit
class TestResetPasswordRequest:
    def test_valid_request(self):
        """Test successful creation of ResetPasswordRequest."""
        request = ResetPasswordRequest(token="token123", new_password="newpass123")
        assert request.token == "token123"
        assert request.new_password == "newpass123"

    def test_missing_fields(self):
        """Test validation error when fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            ResetPasswordRequest(token="token123")
        assert "new_password" in str(exc_info.value)

    def test_password_too_short(self):
        """Test validation error when password is too short."""
        with pytest.raises(ValidationError) as exc_info:
            ResetPasswordRequest(token="token123", new_password="1234567")
        assert "new_password" in str(exc_info.value)


@pytest.mark.unit
class TestLessonCompleteResponse:
    def test_valid_response(self):
        """Test successful creation of LessonCompleteResponse."""
        response = LessonCompleteResponse(new_course_progress_percent=75)
        assert response.new_course_progress_percent == 75