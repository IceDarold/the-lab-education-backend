import pytest
from pydantic import ValidationError
from src.schemas.api import CreateCourseRequest, CreateModuleRequest, CreateLessonRequest


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