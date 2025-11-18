"""
ComfyUI MCP Server - AI-powered image generation for Godot games.

This package provides a Model Context Protocol (MCP) server that bridges
ComfyUI's workflow-based image generation with Godot game development.
"""

from __future__ import annotations

from comfyui_mcp.models import (
    TemplateParameter,
    WorkflowNode,
    WorkflowPrompt,
    WorkflowTemplate,
)

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "WorkflowNode",
    "WorkflowPrompt",
    "TemplateParameter",
    "WorkflowTemplate",
]
