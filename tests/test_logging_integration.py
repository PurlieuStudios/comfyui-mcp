"""Tests for logging integration in ComfyUIClient."""

from __future__ import annotations

import logging

import pytest

from comfyui_mcp.comfyui_client import ComfyUIClient
from comfyui_mcp.models import ComfyUIConfig


class TestLoggingIntegration:
    """Test logging integration in ComfyUIClient."""

    @pytest.mark.asyncio
    async def test_client_has_logger(self):
        """Test that ComfyUIClient has a logger."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        assert hasattr(client, "logger")
        assert isinstance(client.logger, logging.Logger)
        assert client.logger.name == "comfyui_mcp.comfyui_client"

        await client.close()

    @pytest.mark.asyncio
    async def test_logs_client_initialization(self, caplog):
        """Test that client initialization is logged."""
        caplog.set_level(logging.DEBUG)

        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        # Should log initialization
        assert any(
            "ComfyUIClient initialized" in record.message for record in caplog.records
        )

        await client.close()

    @pytest.mark.asyncio
    async def test_logs_session_creation(self, caplog):
        """Test that session creation is logged."""
        caplog.set_level(logging.DEBUG)

        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        # Access session property to trigger creation
        _ = client.session

        # Should log session creation
        assert any(
            "Creating aiohttp session" in record.message for record in caplog.records
        )

        await client.close()

    @pytest.mark.asyncio
    async def test_logs_session_close(self, caplog):
        """Test that session close is logged."""
        caplog.set_level(logging.DEBUG)

        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)
        _ = client.session  # Create session

        await client.close()

        # Should log session close
        assert any(
            "Closing aiohttp session" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_api_requests(self, caplog, aiohttp_server):
        """Test that API requests are logged."""
        from aiohttp import web

        caplog.set_level(logging.INFO)

        async def queue_handler(request):
            return web.json_response({"queue_running": [], "queue_pending": []})

        app = web.Application()
        app.router.add_get("/queue", queue_handler)

        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        client = ComfyUIClient(config)

        # Make a request
        await client.validate_connection()

        # Should log the API request
        assert any("/queue" in record.message for record in caplog.records)

        await client.close()

    @pytest.mark.asyncio
    async def test_logs_errors(self, caplog):
        """Test that errors are logged."""
        caplog.set_level(logging.ERROR)

        config = ComfyUIConfig(url="http://127.0.0.1:9999")
        client = ComfyUIClient(config)

        # This should fail and log an error
        try:
            await client.validate_connection()
        except Exception:
            pass  # Expected to fail

        # Should log error
        assert any(record.levelname == "ERROR" for record in caplog.records)

        await client.close()

    @pytest.mark.asyncio
    async def test_log_levels_configurable(self):
        """Test that log levels can be configured."""
        logger = logging.getLogger("comfyui_mcp.comfyui_client")
        original_level = logger.level

        try:
            # Set to DEBUG
            logger.setLevel(logging.DEBUG)
            assert logger.level == logging.DEBUG

            # Set to INFO
            logger.setLevel(logging.INFO)
            assert logger.level == logging.INFO

            # Set to WARNING
            logger.setLevel(logging.WARNING)
            assert logger.level == logging.WARNING
        finally:
            # Restore original level
            logger.setLevel(original_level)

    @pytest.mark.asyncio
    async def test_logs_include_context(self, caplog):
        """Test that logs include contextual information."""
        caplog.set_level(logging.DEBUG)

        config = ComfyUIConfig(url="http://127.0.0.1:8188", timeout=30.0)
        client = ComfyUIClient(config)

        # Should include config details in initialization log
        init_records = [r for r in caplog.records if "initialized" in r.message]
        assert len(init_records) > 0
        # Context should include URL
        assert any("127.0.0.1:8188" in r.message for r in init_records)

        await client.close()

    @pytest.mark.asyncio
    async def test_no_sensitive_data_in_logs(self, caplog):
        """Test that sensitive data like API keys are not logged."""
        caplog.set_level(logging.DEBUG)

        config = ComfyUIConfig(
            url="http://127.0.0.1:8188", api_key="super-secret-api-key-12345"
        )
        client = ComfyUIClient(config)

        _ = client.session  # Trigger session creation

        # API key should NOT appear in any logs
        for record in caplog.records:
            assert "super-secret-api-key-12345" not in record.message
            # Should show redacted or masked
            if "api_key" in record.message:
                assert "***" in record.message or "redacted" in record.message.lower()

        await client.close()
