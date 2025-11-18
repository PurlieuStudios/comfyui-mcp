"""Tests for retry logic with exponential backoff."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientConnectorError, ClientResponseError, ServerTimeoutError

from comfyui_mcp.retry import retry_with_backoff


class TestRetryWithBackoff:
    """Test retry decorator with exponential backoff."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """Test that function succeeds without retries when no error occurs."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()

        assert result == "success"
        assert call_count == 1  # Only called once, no retries

    @pytest.mark.asyncio
    async def test_retries_on_connection_error(self):
        """Test that function retries on ClientConnectorError."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ClientConnectorError(MagicMock(), OSError("Connection failed"))
            return "success"

        result = await failing_then_success()

        assert result == "success"
        assert call_count == 3  # Failed twice, succeeded on third

    @pytest.mark.asyncio
    async def test_retries_on_timeout_error(self):
        """Test that function retries on ServerTimeoutError."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def timeout_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ServerTimeoutError()
            return "success"

        result = await timeout_then_success()

        assert result == "success"
        assert call_count == 2  # Failed once, succeeded on second

    @pytest.mark.asyncio
    async def test_retries_on_500_server_error(self):
        """Test that function retries on 500 server error."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def server_error_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                # Create ClientResponseError for 500 status
                request_info = MagicMock()
                request_info.url = "http://test.com"
                request_info.method = "GET"
                history = ()
                raise ClientResponseError(
                    request_info=request_info,
                    history=history,
                    status=500,
                    message="Internal Server Error",
                )
            return "success"

        result = await server_error_then_success()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_429_rate_limit(self):
        """Test that function retries on 429 rate limit error."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def rate_limit_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                request_info = MagicMock()
                request_info.url = "http://test.com"
                request_info.method = "GET"
                history = ()
                raise ClientResponseError(
                    request_info=request_info,
                    history=history,
                    status=429,
                    message="Too Many Requests",
                )
            return "success"

        result = await rate_limit_then_success()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_does_not_retry_on_400_client_error(self):
        """Test that function does NOT retry on 400 client error."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def client_error():
            nonlocal call_count
            call_count += 1
            request_info = MagicMock()
            request_info.url = "http://test.com"
            request_info.method = "GET"
            history = ()
            raise ClientResponseError(
                request_info=request_info,
                history=history,
                status=400,
                message="Bad Request",
            )

        with pytest.raises(ClientResponseError) as exc_info:
            await client_error()

        assert exc_info.value.status == 400
        assert call_count == 1  # Should NOT retry on 4xx errors

    @pytest.mark.asyncio
    async def test_does_not_retry_on_404_not_found(self):
        """Test that function does NOT retry on 404 not found."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def not_found():
            nonlocal call_count
            call_count += 1
            request_info = MagicMock()
            request_info.url = "http://test.com"
            request_info.method = "GET"
            history = ()
            raise ClientResponseError(
                request_info=request_info,
                history=history,
                status=404,
                message="Not Found",
            )

        with pytest.raises(ClientResponseError) as exc_info:
            await not_found()

        assert exc_info.value.status == 404
        assert call_count == 1  # Should NOT retry on 404

    @pytest.mark.asyncio
    async def test_max_attempts_exhausted(self):
        """Test that function raises error after max_attempts exhausted."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ClientConnectorError(MagicMock(), OSError("Connection failed"))

        with pytest.raises(ClientConnectorError):
            await always_fails()

        assert call_count == 3  # Should try exactly max_attempts times

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that backoff timing follows exponential pattern with jitter."""
        call_times = []

        @retry_with_backoff(max_attempts=4, max_wait=10)
        async def track_timing():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 4:
                raise ClientConnectorError(MagicMock(), OSError("Connection failed"))
            return "success"

        # Patch asyncio.sleep to record wait times
        wait_times = []

        async def mock_sleep(seconds):
            wait_times.append(seconds)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            result = await track_timing()

        assert result == "success"
        assert len(wait_times) == 3  # 3 retries = 3 sleeps

        # Verify exponential backoff pattern (with some tolerance for jitter)
        # First retry: ~2^0 = 1 second + jitter (0-1)
        # Second retry: ~2^1 = 2 seconds + jitter (0-1)
        # Third retry: ~2^2 = 4 seconds + jitter (0-1)
        assert 1 <= wait_times[0] <= 2  # 2^0 + jitter
        assert 2 <= wait_times[1] <= 3  # 2^1 + jitter
        assert 4 <= wait_times[2] <= 5  # 2^2 + jitter

    @pytest.mark.asyncio
    async def test_max_wait_time_enforced(self):
        """Test that max_wait time is enforced."""
        wait_times: list[float] = []

        @retry_with_backoff(max_attempts=10, max_wait=5)
        async def test_max_wait():
            if len(wait_times) < 5:
                raise ClientConnectorError(MagicMock(), OSError("Connection failed"))
            return "success"

        async def mock_sleep(seconds):
            wait_times.append(seconds)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            result = await test_max_wait()

        assert result == "success"
        # All wait times should be <= max_wait
        for wait_time in wait_times:
            assert wait_time <= 5

    @pytest.mark.asyncio
    async def test_custom_max_attempts(self):
        """Test that custom max_attempts is respected."""
        call_count = 0

        @retry_with_backoff(max_attempts=5)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ServerTimeoutError()

        with pytest.raises(ServerTimeoutError):
            await always_fails()

        assert call_count == 5  # Should respect custom max_attempts

    @pytest.mark.asyncio
    async def test_retries_multiple_error_types(self):
        """Test that function retries on different error types."""
        call_count = 0
        errors = [
            ClientConnectorError(MagicMock(), OSError("Connection failed")),
            ServerTimeoutError(),
        ]

        @retry_with_backoff(max_attempts=4)
        async def multiple_errors():
            nonlocal call_count
            if call_count < len(errors):
                error = errors[call_count]
                call_count += 1
                raise error
            call_count += 1
            return "success"

        result = await multiple_errors()

        assert result == "success"
        assert call_count == 3  # 2 errors + 1 success

    @pytest.mark.asyncio
    async def test_preserves_function_signature(self):
        """Test that decorator preserves function signature and metadata."""

        @retry_with_backoff(max_attempts=3)
        async def documented_function(arg1: str, arg2: int = 10) -> str:
            """This is a documented function."""
            return f"{arg1}-{arg2}"

        # Test function works correctly
        result = await documented_function("test", 20)
        assert result == "test-20"

        # Test default argument
        result = await documented_function("test")
        assert result == "test-10"

        # Verify function name and docstring are preserved
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ is not None
        assert "documented function" in documented_function.__doc__
