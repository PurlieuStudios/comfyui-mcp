"""Main MCP server implementation for comfyui-mcp.

This module provides the MCP (Model Context Protocol) server that exposes
ComfyUI workflow generation capabilities as MCP tools. The server handles:
- Image generation from workflow templates
- Workflow template management and discovery
- Workflow execution status monitoring
- Workflow cancellation
- Custom workflow loading

The server communicates via stdio transport and integrates with:
- ComfyUIClient for API communication
- WorkflowTemplateManager for template management
- ImageGenerator for workflow orchestration

Example:
    >>> from comfyui_mcp.server import main
    >>> main()  # Starts the MCP server
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from comfyui_mcp.comfyui_client import ComfyUIClient
from comfyui_mcp.config import load_config
from comfyui_mcp.image_generator import ImageGenerator
from comfyui_mcp.models import ComfyUIConfig
from comfyui_mcp.template_manager import WorkflowTemplateManager


class ComfyUIMCPServer:
    """MCP server for ComfyUI workflow generation.

    This server exposes ComfyUI capabilities through the Model Context Protocol,
    allowing AI assistants and other MCP clients to generate images using
    workflow templates.

    The server provides tools for:
    - Generating images from templates
    - Listing available workflow templates
    - Monitoring workflow execution status
    - Cancelling running workflows
    - Loading custom workflow files

    Attributes:
        server: MCP Server instance handling protocol communication
        config: ComfyUI configuration (URL, output dir, etc.)
        client: ComfyUI API client for backend communication
        template_manager: Manager for workflow templates
        image_generator: Orchestrator for image generation workflows

    Example:
        >>> config = ComfyUIConfig(url="http://localhost:8188")
        >>> server = ComfyUIMCPServer(config=config, template_dir=Path("./workflows"))
        >>> await server.run()
    """

    def __init__(self, config: ComfyUIConfig, template_dir: Path | None = None) -> None:
        """Initialize the ComfyUI MCP server.

        Args:
            config: ComfyUI configuration with API URL and settings
            template_dir: Directory containing workflow templates.
                        If None, uses default workflows directory.

        Example:
            >>> config = ComfyUIConfig(url="http://localhost:8188")
            >>> server = ComfyUIMCPServer(
            ...     config=config,
            ...     template_dir=Path("./workflows")
            ... )
        """
        self.config = config
        self.server = Server("comfyui-mcp")

        # Initialize components
        self.client = ComfyUIClient(config)

        # Setup template directory
        if template_dir is None:
            template_dir = Path.cwd() / "workflows"

        self.template_manager = WorkflowTemplateManager(template_dir)
        self.image_generator = ImageGenerator(
            client=self.client,
            template_manager=self.template_manager,
        )

        # Register MCP handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers for tools and resources."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools.

            Returns:
                List of Tool definitions for MCP protocol
            """
            return await self._list_tools_handler()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool invocations.

            Args:
                name: Tool name to invoke
                arguments: Tool arguments as dictionary

            Returns:
                List of TextContent responses
            """
            return await self._call_tool_handler(name, arguments)

    async def _list_tools_handler(self) -> list[Tool]:
        """Internal handler for listing tools.

        Returns:
            List of available MCP tools with their schemas
        """
        return [
            Tool(
                name="generate_image",
                description="Generate images using ComfyUI workflow templates. "
                "Provide a template ID and parameters to create images.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "ID (filename without extension) of the workflow template to use",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Parameters to substitute into the template (e.g., prompt, seed, width, height)",
                            "additionalProperties": True,
                        },
                    },
                    "required": ["template_id"],
                },
            ),
            Tool(
                name="list_workflows",
                description="List all available workflow templates with their descriptions and parameters",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_workflow_status",
                description="Get the execution status of a workflow by prompt ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt_id": {
                            "type": "string",
                            "description": "The prompt ID returned when the workflow was submitted",
                        },
                    },
                    "required": ["prompt_id"],
                },
            ),
            Tool(
                name="cancel_workflow",
                description="Cancel a running or queued workflow by prompt ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt_id": {
                            "type": "string",
                            "description": "The prompt ID of the workflow to cancel",
                        },
                    },
                    "required": ["prompt_id"],
                },
            ),
            Tool(
                name="load_workflow",
                description="Load a custom workflow from a JSON file. Returns the loaded workflow definition.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_path": {
                            "type": "string",
                            "description": "Path to the workflow JSON file",
                        },
                    },
                    "required": ["workflow_path"],
                },
            ),
        ]

    async def _call_tool_handler(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Internal handler for tool invocations.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            if name == "generate_image":
                return await self._handle_generate_image(arguments)
            elif name == "list_workflows":
                return await self._handle_list_workflows(arguments)
            elif name == "get_workflow_status":
                return await self._handle_get_workflow_status(arguments)
            elif name == "cancel_workflow":
                return await self._handle_cancel_workflow(arguments)
            elif name == "load_workflow":
                return await self._handle_load_workflow(arguments)
            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2),
                    )
                ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Tool execution failed: {str(e)}"}, indent=2
                    ),
                )
            ]

    async def _handle_generate_image(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle generate_image tool invocation.

        Args:
            arguments: Tool arguments with template_id and parameters

        Returns:
            TextContent with generation result
        """
        template_id = arguments.get("template_id")
        parameters = arguments.get("parameters", {})

        if not template_id:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Missing required argument: template_id"}, indent=2
                    ),
                )
            ]

        try:
            result = await self.image_generator.generate_from_template(
                template_id=template_id,
                parameters=parameters,
            )

            response_data = {
                "prompt_id": result.prompt_id,
                "images": result.images,
                "metadata": result.metadata,
                "execution_time": result.execution_time,
            }

            return [
                TextContent(
                    type="text",
                    text=json.dumps(response_data, indent=2),
                )
            ]
        except FileNotFoundError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Template not found: {str(e)}"}, indent=2
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Generation failed: {str(e)}"}, indent=2
                    ),
                )
            ]

    async def _handle_list_workflows(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle list_workflows tool invocation.

        Args:
            arguments: Tool arguments (none expected)

        Returns:
            TextContent with list of available workflows
        """
        try:
            templates = self.template_manager.list_templates()

            workflows = []
            for template_id in templates:
                template = self.template_manager.load_template(template_id)
                workflows.append(
                    {
                        "id": template_id,
                        "name": template.name,
                        "description": template.description,
                        "parameters": {
                            name: {
                                "type": param.type,
                                "description": param.description,
                                "default": param.default,
                                "required": param.required,
                            }
                            for name, param in template.parameters.items()
                        },
                    }
                )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(workflows, indent=2),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Failed to list workflows: {str(e)}"}, indent=2
                    ),
                )
            ]

    async def _handle_get_workflow_status(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle get_workflow_status tool invocation.

        Args:
            arguments: Tool arguments with prompt_id

        Returns:
            TextContent with workflow status
        """
        prompt_id = arguments.get("prompt_id")

        if not prompt_id:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Missing required argument: prompt_id"}, indent=2
                    ),
                )
            ]

        try:
            status = await self.client.get_queue_status()

            return [
                TextContent(
                    type="text",
                    text=json.dumps(status, indent=2),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Failed to get status: {str(e)}"}, indent=2
                    ),
                )
            ]

    async def _handle_cancel_workflow(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle cancel_workflow tool invocation.

        Args:
            arguments: Tool arguments with prompt_id

        Returns:
            TextContent with cancellation result
        """
        prompt_id = arguments.get("prompt_id")

        if not prompt_id:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Missing required argument: prompt_id"}, indent=2
                    ),
                )
            ]

        try:
            success = await self.client.cancel_workflow(prompt_id)

            if success:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "status": "success",
                                "message": f"Workflow {prompt_id} cancelled successfully",
                            },
                            indent=2,
                        ),
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "status": "failed",
                                "message": f"Failed to cancel workflow {prompt_id}",
                            },
                            indent=2,
                        ),
                    )
                ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Cancellation failed: {str(e)}"}, indent=2
                    ),
                )
            ]

    async def _handle_load_workflow(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle load_workflow tool invocation.

        Args:
            arguments: Tool arguments with workflow_path

        Returns:
            TextContent with loaded workflow
        """
        workflow_path = arguments.get("workflow_path")

        if not workflow_path:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Missing required argument: workflow_path"}, indent=2
                    ),
                )
            ]

        try:
            path = Path(workflow_path)
            if not path.exists():
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": f"Workflow file not found: {workflow_path}"},
                            indent=2,
                        ),
                    )
                ]

            workflow_data = json.loads(path.read_text())

            # Check if it has a prompt field (standard ComfyUI format)
            if "prompt" in workflow_data:
                nodes_data = workflow_data["prompt"]
                node_count = len(nodes_data) if isinstance(nodes_data, dict) else 0

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "status": "success",
                                "message": f"Workflow loaded from {workflow_path}",
                                "nodes": node_count,
                                "workflow": workflow_data,
                            },
                            indent=2,
                        ),
                    )
                ]
            else:
                # Just return the raw data
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "status": "loaded",
                                "workflow": workflow_data,
                            },
                            indent=2,
                        ),
                    )
                ]
        except json.JSONDecodeError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Invalid JSON in workflow file: {str(e)}"}, indent=2
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Failed to load workflow: {str(e)}"}, indent=2
                    ),
                )
            ]

    async def run(self) -> None:
        """Run the MCP server using stdio transport.

        This method starts the server and handles communication via stdin/stdout
        following the MCP protocol. It runs until the client disconnects or
        the server is terminated.

        Example:
            >>> server = ComfyUIMCPServer(config=config, template_dir=templates)
            >>> await server.run()
        """
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main() -> None:
    """Main entry point for the comfyui-mcp server.

    Parses command-line arguments, loads configuration, and starts the MCP server.

    Command-line arguments:
        --config: Path to TOML configuration file
        --comfyui-url: ComfyUI server URL (overrides config file)
        --template-dir: Directory containing workflow templates

    Environment variables:
        COMFYUI_URL: ComfyUI server URL
        COMFYUI_OUTPUT_DIR: Output directory for generated images

    Example:
        >>> # Start with default configuration
        >>> main()
        >>>
        >>> # Start with custom config file
        >>> # python -m comfyui_mcp.server --config myconfig.toml
        >>>
        >>> # Start with environment variables
        >>> # COMFYUI_URL=http://localhost:8188 python -m comfyui_mcp.server
    """
    parser = argparse.ArgumentParser(
        description="ComfyUI MCP Server - AI Image Generation"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to TOML configuration file",
    )
    parser.add_argument(
        "--comfyui-url",
        type=str,
        help="ComfyUI server URL (default: http://localhost:8188)",
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        help="Directory containing workflow templates (default: ./workflows)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        # load_config() handles environment and file-based config automatically
        config = load_config()

        # Override with command-line arguments
        if args.comfyui_url:
            # Create new config with updated URL
            config = ComfyUIConfig(
                url=args.comfyui_url,
                api_key=config.api_key,
                timeout=config.timeout,
                output_dir=config.output_dir,
            )

    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        print("Using default configuration...", file=sys.stderr)
        config = ComfyUIConfig(url="http://localhost:8188")

    # Create server
    template_dir = args.template_dir if args.template_dir else None
    server = ComfyUIMCPServer(config=config, template_dir=template_dir)

    # Run server
    import asyncio

    asyncio.run(server.run())


if __name__ == "__main__":
    main()
