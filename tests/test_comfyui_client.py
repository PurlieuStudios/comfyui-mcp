"""Tests for ComfyUI API client with aiohttp session management."""

from __future__ import annotations

import pytest
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession

from comfyui_mcp.comfyui_client import ComfyUIClient
from comfyui_mcp.models import ComfyUIConfig, WorkflowNode, WorkflowPrompt


class TestComfyUIClientInitialization:
    """Test ComfyUIClient initialization and configuration."""

    def test_create_client_with_config(self):
        """Test creating client with valid configuration."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        assert client.config == config
        assert client.config.url == "http://127.0.0.1:8188"
        assert client.config.timeout == 120.0  # Default timeout

    def test_create_client_with_custom_timeout(self):
        """Test creating client with custom timeout."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188", timeout=60.0)
        client = ComfyUIClient(config)

        assert client.config.timeout == 60.0

    def test_create_client_with_api_key(self):
        """Test creating client with API key."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188", api_key="test-api-key-123")
        client = ComfyUIClient(config)

        assert client.config.api_key == "test-api-key-123"

    def test_create_client_with_output_dir(self):
        """Test creating client with output directory."""
        config = ComfyUIConfig(
            url="http://127.0.0.1:8188", output_dir="/path/to/output"
        )
        client = ComfyUIClient(config)

        assert client.config.output_dir == "/path/to/output"


class TestComfyUIClientSessionManagement:
    """Test ComfyUIClient aiohttp session management."""

    @pytest.mark.asyncio
    async def test_session_property_creates_session(self):
        """Test that accessing session property creates aiohttp session."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        session = client.session
        assert isinstance(session, ClientSession)
        assert not session.closed

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_session_property_reuses_session(self):
        """Test that session property reuses existing session."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        session1 = client.session
        session2 = client.session

        assert session1 is session2  # Same instance

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_close_closes_session(self):
        """Test that close() properly closes the aiohttp session."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        session = client.session
        assert not session.closed

        await client.close()
        assert session.closed

    @pytest.mark.asyncio
    async def test_close_handles_no_session(self):
        """Test that close() handles case when no session exists."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        # Should not raise error even if session was never created
        await client.close()

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        """Test that close() can be called multiple times safely."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        session = client.session
        await client.close()
        await client.close()  # Should not raise error

        assert session.closed


class TestComfyUIClientContextManager:
    """Test ComfyUIClient async context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager_creates_and_closes_session(self):
        """Test async context manager creates and closes session."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")

        async with ComfyUIClient(config) as client:
            assert isinstance(client, ComfyUIClient)
            session = client.session
            assert isinstance(session, ClientSession)
            assert not session.closed

        # Session should be closed after exiting context
        assert session.closed

    @pytest.mark.asyncio
    async def test_context_manager_returns_self(self):
        """Test that __aenter__ returns the client instance."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        async with client as entered_client:
            assert entered_client is client

    @pytest.mark.asyncio
    async def test_context_manager_closes_on_exception(self):
        """Test that session is closed even if exception occurs."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        session_ref = None

        try:
            async with ComfyUIClient(config) as client:
                session_ref = client.session
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Session should still be closed
        assert session_ref is not None
        assert session_ref.closed


class TestComfyUIClientSessionConfiguration:
    """Test ComfyUIClient session configuration with timeouts and headers."""

    @pytest.mark.asyncio
    async def test_session_timeout_configuration(self):
        """Test that session uses configured timeout."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188", timeout=60.0)
        client = ComfyUIClient(config)

        session = client.session
        assert session.timeout.total == 60.0

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_session_headers_with_api_key(self):
        """Test that session headers include API key if provided."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188", api_key="test-api-key-123")
        client = ComfyUIClient(config)

        session = client.session
        assert "Authorization" in session.headers
        assert session.headers["Authorization"] == "Bearer test-api-key-123"

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_session_headers_without_api_key(self):
        """Test that session headers do not include Authorization if no API key."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188")
        client = ComfyUIClient(config)

        session = client.session
        assert "Authorization" not in session.headers

        # Clean up
        await client.close()


class TestComfyUIClientIntegration:
    """Integration tests for ComfyUIClient."""

    @pytest.mark.asyncio
    async def test_multiple_clients_independent(self):
        """Test that multiple client instances are independent."""
        config1 = ComfyUIConfig(url="http://127.0.0.1:8188", timeout=60.0)
        config2 = ComfyUIConfig(url="http://192.168.1.100:8188", timeout=30.0)

        client1 = ComfyUIClient(config1)
        client2 = ComfyUIClient(config2)

        session1 = client1.session
        session2 = client2.session

        assert session1 is not session2
        assert client1.config.timeout == 60.0
        assert client2.config.timeout == 30.0

        # Clean up
        await client1.close()
        await client2.close()

    @pytest.mark.asyncio
    async def test_nested_context_managers(self):
        """Test that nested context managers work correctly."""
        config1 = ComfyUIConfig(url="http://127.0.0.1:8188")
        config2 = ComfyUIConfig(url="http://192.168.1.100:8188")

        async with ComfyUIClient(config1) as client1:
            session1 = client1.session
            async with ComfyUIClient(config2) as client2:
                session2 = client2.session
                assert not session1.closed
                assert not session2.closed
                assert session1 is not session2

            # client2 session should be closed
            assert session2.closed
            assert not session1.closed

        # Both sessions should be closed
        assert session1.closed
        assert session2.closed


class TestComfyUIClientConnectionValidation:
    """Test ComfyUI client connection validation and health checks."""

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, aiohttp_server):
        """Test successful connection validation to ComfyUI server."""
        from aiohttp import web

        # Create mock ComfyUI server
        app = web.Application()

        async def queue_handler(request):
            return web.json_response({"queue_running": [], "queue_pending": []})

        app.router.add_get("/queue", queue_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Validate connection
        is_connected = await comfy_client.validate_connection()

        assert is_connected is True

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_validate_connection_server_unreachable(self):
        """Test connection validation when server is unreachable."""
        config = ComfyUIConfig(url="http://127.0.0.1:9999")  # Non-existent server
        client = ComfyUIClient(config)

        is_connected = await client.validate_connection()

        assert is_connected is False

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_validate_connection_timeout(self):
        """Test connection validation with timeout."""
        config = ComfyUIConfig(url="http://10.255.255.1:8188", timeout=0.1)
        client = ComfyUIClient(config)

        is_connected = await client.validate_connection()

        assert is_connected is False

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_validate_connection_http_error(self, aiohttp_server):
        """Test connection validation when server returns HTTP error."""
        from aiohttp import web

        # Create mock server that returns 500 error
        app = web.Application()

        async def queue_handler(request):
            return web.Response(status=500, text="Internal Server Error")

        app.router.add_get("/queue", queue_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Should still return False on HTTP errors
        is_connected = await comfy_client.validate_connection()

        assert is_connected is False

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_health_check_returns_server_info(self, aiohttp_server):
        """Test health check returns server information."""
        from aiohttp import web

        # Create mock ComfyUI server
        app = web.Application()

        async def queue_handler(request):
            return web.json_response({"queue_running": [], "queue_pending": []})

        app.router.add_get("/queue", queue_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Get health check info
        health_info = await comfy_client.health_check()

        assert health_info["connected"] is True
        assert "url" in health_info
        assert health_info["url"] == f"{config.url.rstrip('/')}/queue"
        assert "status_code" in health_info
        assert health_info["status_code"] == 200

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_health_check_server_unreachable(self):
        """Test health check when server is unreachable."""
        config = ComfyUIConfig(url="http://127.0.0.1:9999")
        client = ComfyUIClient(config)

        health_info = await client.health_check()

        assert health_info["connected"] is False
        assert health_info["url"] == "http://127.0.0.1:9999/queue"
        assert "error" in health_info

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_health_check_with_custom_endpoint(self, aiohttp_server):
        """Test health check can use custom endpoint."""
        from aiohttp import web

        # Create mock server with custom endpoint
        app = web.Application()

        async def system_stats_handler(request):
            return web.json_response({"system": {"os": "linux"}})

        app.router.add_get("/system_stats", system_stats_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Health check with custom endpoint
        health_info = await comfy_client.health_check(endpoint="/system_stats")

        assert health_info["connected"] is True
        assert health_info["status_code"] == 200

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_validate_connection_called_multiple_times(self, aiohttp_server):
        """Test that validate_connection can be called multiple times."""
        from aiohttp import web

        app = web.Application()

        async def queue_handler(request):
            return web.json_response({"queue_running": [], "queue_pending": []})

        app.router.add_get("/queue", queue_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Call multiple times
        result1 = await comfy_client.validate_connection()
        result2 = await comfy_client.validate_connection()
        result3 = await comfy_client.validate_connection()

        assert result1 is True
        assert result2 is True
        assert result3 is True

        # Clean up
        await comfy_client.close()


class TestComfyUIClientWorkflowSubmission:
    """Test ComfyUI client workflow submission to /prompt endpoint."""

    @pytest.mark.asyncio
    async def test_submit_workflow_success(self, aiohttp_server):
        """Test successful workflow submission."""
        from aiohttp import web

        # Create mock ComfyUI server
        app = web.Application()

        async def prompt_handler(request):
            await request.json()
            return web.json_response({"prompt_id": "test-prompt-123"})

        app.router.add_post("/prompt", prompt_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Create test workflow
        workflow = WorkflowPrompt(
            nodes={
                "1": WorkflowNode(
                    class_type="KSampler", inputs={"seed": 123, "steps": 20}
                )
            }
        )

        # Submit workflow
        response = await comfy_client.submit_workflow(workflow)

        assert "prompt_id" in response
        assert response["prompt_id"] == "test-prompt-123"

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_submit_workflow_with_client_id(self, aiohttp_server):
        """Test workflow submission includes client_id when provided."""
        from aiohttp import web

        received_data = {}

        async def prompt_handler(request):
            nonlocal received_data
            received_data = await request.json()
            return web.json_response({"prompt_id": "test-prompt-456"})

        app = web.Application()
        app.router.add_post("/prompt", prompt_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Create workflow with client_id
        workflow = WorkflowPrompt(
            nodes={"1": WorkflowNode(class_type="KSampler", inputs={"seed": 456})},
            client_id="my-test-client",
        )

        # Submit workflow
        response = await comfy_client.submit_workflow(workflow)

        assert response["prompt_id"] == "test-prompt-456"
        assert "client_id" in received_data
        assert received_data["client_id"] == "my-test-client"

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_submit_workflow_sends_correct_format(self, aiohttp_server):
        """Test that workflow is sent in correct ComfyUI API format."""
        from aiohttp import web

        received_data = {}

        async def prompt_handler(request):
            nonlocal received_data
            received_data = await request.json()
            return web.json_response({"prompt_id": "test-prompt-789"})

        app = web.Application()
        app.router.add_post("/prompt", prompt_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Create workflow
        workflow = WorkflowPrompt(
            nodes={
                "1": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "model.safetensors"},
                ),
                "2": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": 789, "model": ["1", 0]},
                ),
            }
        )

        # Submit workflow
        await comfy_client.submit_workflow(workflow)

        # Verify format
        assert "prompt" in received_data
        assert "1" in received_data["prompt"]
        assert "2" in received_data["prompt"]
        assert received_data["prompt"]["1"]["class_type"] == "CheckpointLoaderSimple"
        assert received_data["prompt"]["2"]["class_type"] == "KSampler"
        assert received_data["prompt"]["2"]["inputs"]["seed"] == 789

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_submit_workflow_server_error(self, aiohttp_server):
        """Test workflow submission handles server errors."""
        from aiohttp import web

        async def prompt_handler(request):
            return web.Response(status=500, text="Internal Server Error")

        app = web.Application()
        app.router.add_post("/prompt", prompt_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Create workflow
        workflow = WorkflowPrompt(
            nodes={"1": WorkflowNode(class_type="KSampler", inputs={"seed": 1})}
        )

        # Should raise exception on server error
        with pytest.raises(ClientResponseError):
            await comfy_client.submit_workflow(workflow)

        # Clean up
        await comfy_client.close()

    @pytest.mark.asyncio
    async def test_submit_workflow_connection_error(self):
        """Test workflow submission handles connection errors."""
        config = ComfyUIConfig(url="http://127.0.0.1:9999")
        client = ComfyUIClient(config)

        # Create workflow
        workflow = WorkflowPrompt(
            nodes={"1": WorkflowNode(class_type="KSampler", inputs={"seed": 1})}
        )

        # Should raise exception on connection error
        with pytest.raises(ClientConnectorError):
            await client.submit_workflow(workflow)

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_submit_workflow_complex_workflow(self, aiohttp_server):
        """Test submitting complex workflow with multiple nodes."""
        from aiohttp import web

        async def prompt_handler(request):
            return web.json_response({"prompt_id": "complex-workflow-123"})

        app = web.Application()
        app.router.add_post("/prompt", prompt_handler)

        # Start server
        server = await aiohttp_server(app)
        config = ComfyUIConfig(url=str(server.make_url("/")))
        comfy_client = ComfyUIClient(config)

        # Create complex workflow
        workflow = WorkflowPrompt(
            nodes={
                "1": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "v1-5-pruned.safetensors"},
                ),
                "2": WorkflowNode(
                    class_type="CLIPTextEncode",
                    inputs={"text": "a warrior", "clip": ["1", 1]},
                ),
                "3": WorkflowNode(
                    class_type="KSampler",
                    inputs={
                        "seed": 12345,
                        "steps": 20,
                        "cfg": 7.5,
                        "model": ["1", 0],
                        "positive": ["2", 0],
                    },
                ),
                "4": WorkflowNode(class_type="SaveImage", inputs={"images": ["3", 0]}),
            }
        )

        # Submit workflow
        response = await comfy_client.submit_workflow(workflow)

        assert "prompt_id" in response
        assert response["prompt_id"] == "complex-workflow-123"

        # Clean up
        await comfy_client.close()
