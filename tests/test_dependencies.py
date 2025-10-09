import pytest
from fastapi import HTTPException, status
from src.dependencies import validate_content_size


@pytest.mark.unit
class TestValidateContentSize:
    def test_validate_content_size_valid(self):
        """Test validating content within size limit."""
        content = "Hello World"  # Small content
        max_size_mb = 10

        result = validate_content_size(content, max_size_mb)

        assert result == content

    def test_validate_content_size_at_limit(self):
        """Test validating content exactly at size limit."""
        # Create content exactly at 1MB
        content = "a" * (1024 * 1024)  # 1MB in bytes
        max_size_mb = 1

        result = validate_content_size(content, max_size_mb)

        assert result == content

    def test_validate_content_size_exceeds_limit(self):
        """Test validating content that exceeds size limit."""
        # Create content over 1MB
        content = "a" * (1024 * 1024 + 1)  # 1MB + 1 byte
        max_size_mb = 1

        with pytest.raises(HTTPException) as exc_info:
            validate_content_size(content, max_size_mb)

        assert exc_info.value.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        assert "Content size (1048577 bytes) exceeds maximum allowed size (1048576 bytes)" in exc_info.value.detail

    def test_validate_content_size_different_max_sizes(self):
        """Test validating content with different max_size_mb values."""
        content = "a" * (512 * 1024)  # 512KB

        # Should pass with 1MB limit
        result = validate_content_size(content, max_size_mb=1)
        assert result == content

        # Should fail with 0.5MB limit
        with pytest.raises(HTTPException) as exc_info:
            validate_content_size(content, max_size_mb=0)

        assert exc_info.value.status_code == status.HTTP_413_CONTENT_TOO_LARGE

    def test_validate_content_size_unicode_content(self):
        """Test validating content with unicode characters."""
        # Unicode characters may use more bytes
        content = "Hello 世界 🌍"  # Mix of ASCII and Unicode
        max_size_mb = 10

        result = validate_content_size(content, max_size_mb)

        assert result == content

    def test_validate_content_size_empty_content(self):
        """Test validating empty content."""
        content = ""
        max_size_mb = 10

        result = validate_content_size(content, max_size_mb)

        assert result == content

    def test_validate_content_size_default_max_size(self):
        """Test validating content with default max_size_mb."""
        # Create content over default 10MB
        content = "a" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte

        with pytest.raises(HTTPException) as exc_info:
            validate_content_size(content)  # Use default 10MB

        assert exc_info.value.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        assert "Content size (10485761 bytes) exceeds maximum allowed size (10485760 bytes)" in exc_info.value.detail