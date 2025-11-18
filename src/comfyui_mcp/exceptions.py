"""Custom exception classes for ComfyUI MCP server.

This module defines a hierarchy of exceptions specific to ComfyUI operations,
making it easier to handle different error scenarios appropriately.
"""

from __future__ import annotations

from typing import Any


class ComfyUIError(Exception):
    """Base exception for all ComfyUI-related errors.

    All custom exceptions in this module inherit from this base class,
    allowing users to catch all ComfyUI-specific errors with a single
    except clause if needed.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize the exception with a message and optional context.

        Args:
            message: Human-readable error message
            **kwargs: Additional context attributes to store on the exception
        """
        super().__init__(message)
        # Store any additional context as instance attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


class ComfyUIConnectionError(ComfyUIError):
    """Raised when connection to ComfyUI server fails.

    This includes network errors, connection timeouts, and unreachable servers.

    Example:
        >>> raise ComfyUIConnectionError("Failed to connect to http://127.0.0.1:8188")
    """

    pass


class ComfyUIWorkflowError(ComfyUIError):
    """Raised when there's an error with workflow execution or structure.

    This includes invalid workflow JSON, missing nodes, execution failures, etc.

    Attributes:
        workflow_id: Optional workflow identifier
        node_id: Optional node identifier where error occurred

    Example:
        >>> raise ComfyUIWorkflowError(
        ...     "Workflow validation failed",
        ...     workflow_id="wf-123",
        ...     node_id="node-5"
        ... )
    """

    workflow_id: str | None
    node_id: str | None


class ComfyUIQueueError(ComfyUIError):
    """Raised when there's an error with the ComfyUI queue operations.

    This includes queue full errors, prompt not found, cancellation failures, etc.

    Attributes:
        prompt_id: Optional prompt identifier

    Example:
        >>> raise ComfyUIQueueError("Prompt not found", prompt_id="prompt-456")
    """

    prompt_id: str | None


class ComfyUIValidationError(ComfyUIError):
    """Raised when input validation fails.

    This includes invalid parameters, malformed URLs, invalid config values, etc.

    Attributes:
        field: Optional field name that failed validation
        value: Optional invalid value that was provided

    Example:
        >>> raise ComfyUIValidationError(
        ...     "URL must start with http:// or https://",
        ...     field="url",
        ...     value="ftp://example.com"
        ... )
    """

    field: str | None
    value: Any | None


__all__ = [
    "ComfyUIError",
    "ComfyUIConnectionError",
    "ComfyUIWorkflowError",
    "ComfyUIQueueError",
    "ComfyUIValidationError",
]
