"""
ComfyUI MCP Server - AI-powered image generation for Godot games.

This package provides a Model Context Protocol (MCP) server that bridges
ComfyUI's workflow-based image generation with Godot game development.
"""

from __future__ import annotations

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

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "WorkflowNode",
    "WorkflowPrompt",
    "GenerationResult",
    "GenerationRequest",
    "ComfyUIConfig",
    "WorkflowState",
    "WorkflowStatus",
    "TemplateParameter",
    "WorkflowTemplate",
]
