import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.core.utils import finalize_supabase_result
from src.core.errors import ExternalServiceError


class TestFinalizeSupabaseResult:
    @pytest.mark.asyncio
    async def test_finalize_sync_result(self):
        """Test finalizing a synchronous result without execute or await."""
        result = {"data": "test"}

        final_result = await finalize_supabase_result(result)

        assert final_result == result

    @pytest.mark.asyncio
    async def test_finalize_result_with_execute(self):
        """Test finalizing a result with execute method."""
        mock_result = MagicMock()
        mock_result.execute.return_value = {"executed": True}

        final_result = await finalize_supabase_result(mock_result)

        mock_result.execute.assert_called_once()
        assert final_result == {"executed": True}

    @pytest.mark.asyncio
    async def test_finalize_async_result(self):
        """Test finalizing an async result with __await__."""
        async def fake_result():
            return {"async": "data"}

        final_result = await finalize_supabase_result(fake_result())

        assert final_result == {"async": "data"}

    @pytest.mark.asyncio
    async def test_finalize_result_with_execute_and_async(self):
        """Test finalizing a result with both execute and __await__."""
        mock_result = MagicMock()

        async def fake_execute():
            return {"final": "data"}

        mock_result.execute.return_value = fake_execute()

        final_result = await finalize_supabase_result(mock_result)

        mock_result.execute.assert_called_once()
        assert final_result == {"final": "data"}

    @pytest.mark.asyncio
    async def test_finalize_result_execute_raises_exception(self):
        """Test error handling when execute raises an exception."""
        mock_result = MagicMock()
        mock_result.execute.side_effect = Exception("Execute failed")

        with patch("src.core.utils.logger") as mock_logger:
            with pytest.raises(ExternalServiceError) as exc_info:
                await finalize_supabase_result(mock_result)

        assert "Failed to process Supabase query result: Execute failed" in str(exc_info.value)
        mock_logger.error.assert_called_once_with("Error finalizing Supabase result: Execute failed")

    @pytest.mark.asyncio
    async def test_finalize_async_result_raises_exception(self):
        """Test error handling when awaiting raises an exception."""
        with patch("src.core.utils.logger") as mock_logger:
            with pytest.raises(ExternalServiceError) as exc_info:
                async def failing():
                    raise Exception("Async failed")

                await finalize_supabase_result(failing())

        assert "Failed to process Supabase query result: Async failed" in str(exc_info.value)
        mock_logger.error.assert_called_once_with("Error finalizing Supabase result: Async failed")
