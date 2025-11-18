"""
ComfyUI MCP Server - AI-powered image generation for Godot games.

This package provides a Model Context Protocol (MCP) server that bridges
ComfyUI's workflow-based image generation with Godot game development.
"""

from __future__ import annotations

# Define version first to avoid circular import with cli.py
__version__ = "0.1.0"

from comfyui_mcp.cli import cli
from comfyui_mcp.cli import main as cli_main
from comfyui_mcp.comfyui_client import ComfyUIClient
from comfyui_mcp.config import find_config_file, load_config
from comfyui_mcp.image_generator import ImageGenerator
from comfyui_mcp.models import (
    ComfyUIConfig,
    GenerationRequest,
    GenerationResult,
    TemplateParameter,
    WorkflowNode,
    WorkflowPrompt,
    WorkflowState,
    WorkflowStatus,
    WorkflowTemplate,
)
from comfyui_mcp.retry import retry_with_backoff
from comfyui_mcp.server import ComfyUIMCPServer
from comfyui_mcp.template_manager import WorkflowTemplateManager

__all__ = [
    "__version__",
    "cli",
    "cli_main",
    "ComfyUIClient",
    "ComfyUIMCPServer",
    "ImageGenerator",
    "WorkflowNode",
    "WorkflowPrompt",
    "GenerationResult",
    "GenerationRequest",
    "ComfyUIConfig",
    "WorkflowState",
    "WorkflowStatus",
    "TemplateParameter",
    "WorkflowTemplate",
    "WorkflowTemplateManager",
    "retry_with_backoff",
    "find_config_file",
    "load_config",
]
