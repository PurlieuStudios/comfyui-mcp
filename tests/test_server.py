"""Tests for MCP server implementation.

Tests the MCP server initialization, tool registration, and handler execution
including:
- Server initialization with configuration
- Tool registration (list_tools handler)
- Tool invocation handlers (call_tool)
- Integration with ComfyUIClient and ImageGenerator
- Error handling and response formatting
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from comfyui_mcp import ComfyUIConfig, GenerationResult, WorkflowNode, WorkflowTemplate
from comfyui_mcp.server import ComfyUIMCPServer


class TestServerInitialization:
    """Tests for ComfyUIMCPServer initialization."""

    def test_server_initialization_with_config(self, tmp_path: Path) -> None:
        """Test server initializes correctly with configuration."""
        config = ComfyUIConfig(
            url="http://localhost:8188", output_dir=str(tmp_path / "output")
        )

        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        assert server.config == config
        assert server.client is not None
        assert server.template_manager is not None
        assert server.image_generator is not None
        assert server.server.name == "comfyui-mcp"

    def test_server_initialization_creates_components(self, tmp_path: Path) -> None:
        """Test server creates all required components."""
        config = ComfyUIConfig(url="http://localhost:8188")

        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        # Verify component integration
        assert server.image_generator.client == server.client
        assert server.image_generator.template_manager == server.template_manager


class TestToolRegistration:
    """Tests for MCP tool registration."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, tmp_path: Path) -> None:
        """Test list_tools handler returns all expected tools."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        # Manually call the list_tools handler
        # NOTE: In actual MCP, this would be called by the protocol
        tools = await server._list_tools_handler()

        tool_names = {tool.name for tool in tools}
        expected_tools = {
            "generate_image",
            "list_workflows",
            "get_workflow_status",
            "cancel_workflow",
            "load_workflow",
        }

        assert expected_tools.issubset(tool_names)

    @pytest.mark.asyncio
    async def test_generate_image_tool_schema(self, tmp_path: Path) -> None:
        """Test generate_image tool has correct schema."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        tools = await server._list_tools_handler()
        generate_tool = next(t for t in tools if t.name == "generate_image")

        assert generate_tool.name == "generate_image"
        assert "inputSchema" in generate_tool.model_dump()
        schema = generate_tool.inputSchema
        assert schema["type"] == "object"
        assert "template_id" in schema["properties"]
        assert "parameters" in schema["properties"]


class TestGenerateImageTool:
    """Tests for generate_image MCP tool."""

    @pytest.mark.asyncio
    async def test_generate_image_tool_success(self, tmp_path: Path) -> None:
        """Test generate_image tool executes successfully."""
        # Create a test template
        template = WorkflowTemplate(
            name="Test Template",
            description="Test",
            parameters={},
            nodes={"1": WorkflowNode(class_type="Test", inputs={})},
        )
        template.to_file(tmp_path / "test.json")

        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        # Mock the image generator
        mock_result = GenerationResult(
            prompt_id="test-123",
            images=["image1.png"],
            metadata={},
            execution_time=1.5,
        )
        server.image_generator.generate_from_template = AsyncMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Call the tool
        response = await server._call_tool_handler(
            name="generate_image",
            arguments={"template_id": "test", "parameters": {}},
        )

        assert len(response) == 1
        assert response[0].type == "text"
        result_data = json.loads(response[0].text)
        assert result_data["prompt_id"] == "test-123"
        assert result_data["images"] == ["image1.png"]

    @pytest.mark.asyncio
    async def test_generate_image_tool_missing_template(self, tmp_path: Path) -> None:
        """Test generate_image tool handles missing template."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        response = await server._call_tool_handler(
            name="generate_image",
            arguments={"template_id": "nonexistent", "parameters": {}},
        )

        assert len(response) == 1
        assert response[0].type == "text"
        assert "error" in response[0].text.lower()


class TestListWorkflowsTool:
    """Tests for list_workflows MCP tool."""

    @pytest.mark.asyncio
    async def test_list_workflows_returns_templates(self, tmp_path: Path) -> None:
        """Test list_workflows tool returns available templates."""
        # Create test templates
        template1 = WorkflowTemplate(
            name="Character Portrait",
            description="Generate character portraits",
            parameters={},
            nodes={},
        )
        template1.to_file(tmp_path / "character-portrait.json")

        template2 = WorkflowTemplate(
            name="Item Icon",
            description="Generate item icons",
            parameters={},
            nodes={},
        )
        template2.to_file(tmp_path / "item-icon.json")

        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        response = await server._call_tool_handler(name="list_workflows", arguments={})

        assert len(response) == 1
        assert response[0].type == "text"
        workflows = json.loads(response[0].text)
        assert len(workflows) == 2
        workflow_names = {w["name"] for w in workflows}
        assert "Character Portrait" in workflow_names
        assert "Item Icon" in workflow_names


class TestGetWorkflowStatusTool:
    """Tests for get_workflow_status MCP tool."""

    @pytest.mark.asyncio
    async def test_get_workflow_status_success(self, tmp_path: Path) -> None:
        """Test get_workflow_status tool retrieves status."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        # Mock client.get_queue_status
        mock_status = {
            "queue_running": [{"prompt_id": "test-123", "number": 1}],
            "queue_pending": [],
        }
        server.client.get_queue_status = AsyncMock(return_value=mock_status)  # type: ignore[method-assign]

        response = await server._call_tool_handler(
            name="get_workflow_status",
            arguments={"prompt_id": "test-123"},
        )

        assert len(response) == 1
        assert response[0].type == "text"
        status = json.loads(response[0].text)
        assert "queue_running" in status


class TestCancelWorkflowTool:
    """Tests for cancel_workflow MCP tool."""

    @pytest.mark.asyncio
    async def test_cancel_workflow_success(self, tmp_path: Path) -> None:
        """Test cancel_workflow tool cancels execution."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        # Mock client.cancel_workflow
        server.client.cancel_workflow = AsyncMock(return_value=True)  # type: ignore[method-assign]

        response = await server._call_tool_handler(
            name="cancel_workflow",
            arguments={"prompt_id": "test-123"},
        )

        assert len(response) == 1
        assert response[0].type == "text"
        assert (
            "cancelled" in response[0].text.lower()
            or "canceled" in response[0].text.lower()
        )


class TestLoadWorkflowTool:
    """Tests for load_workflow MCP tool."""

    @pytest.mark.asyncio
    async def test_load_workflow_from_file(self, tmp_path: Path) -> None:
        """Test load_workflow tool loads custom workflow."""
        # Create a custom workflow file
        workflow_file = tmp_path / "custom_workflow.json"
        workflow_data = {
            "prompt": {
                "1": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": "test prompt"},
                }
            }
        }
        workflow_file.write_text(json.dumps(workflow_data))

        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        response = await server._call_tool_handler(
            name="load_workflow",
            arguments={"workflow_path": str(workflow_file)},
        )

        assert len(response) == 1
        assert response[0].type == "text"
        result = json.loads(response[0].text)
        assert "prompt" in result or "loaded" in response[0].text.lower()


class TestServerRun:
    """Tests for server execution."""

    @pytest.mark.asyncio
    async def test_server_run_initializes_stdio(self, tmp_path: Path) -> None:
        """Test server run method initializes stdio transport."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        # Mock stdio_server and server.run
        with patch("comfyui_mcp.server.stdio_server") as mock_stdio:
            # Setup mock context manager
            mock_stdio.return_value.__aenter__.return_value = (
                MagicMock(),
                MagicMock(),
            )
            mock_stdio.return_value.__aexit__.return_value = AsyncMock()

            # Mock the server.run method
            server.server.run = AsyncMock()

            # Run the server (will immediately exit due to mock)
            await server.run()

            # Verify stdio_server was called
            mock_stdio.assert_called_once()


class TestErrorHandling:
    """Tests for error handling in server."""

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, tmp_path: Path) -> None:
        """Test calling an invalid tool returns error."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        response = await server._call_tool_handler(
            name="invalid_tool_name",
            arguments={},
        )

        assert len(response) == 1
        assert response[0].type == "text"
        assert (
            "error" in response[0].text.lower() or "unknown" in response[0].text.lower()
        )

    @pytest.mark.asyncio
    async def test_tool_with_missing_arguments(self, tmp_path: Path) -> None:
        """Test tool call with missing required arguments."""
        config = ComfyUIConfig(url="http://localhost:8188")
        server = ComfyUIMCPServer(config=config, template_dir=tmp_path)

        response = await server._call_tool_handler(
            name="generate_image",
            arguments={},  # Missing required template_id
        )

        assert len(response) == 1
        assert response[0].type == "text"
        assert "error" in response[0].text.lower()
