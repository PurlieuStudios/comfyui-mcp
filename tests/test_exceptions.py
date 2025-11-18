"""Tests for custom exception classes."""

from __future__ import annotations

import pytest

from comfyui_mcp.exceptions import (
    ComfyUIConnectionError,
    ComfyUIError,
    ComfyUIQueueError,
    ComfyUIValidationError,
    ComfyUIWorkflowError,
)


class TestComfyUIError:
    """Test base ComfyUI exception."""

    def test_base_exception_message(self):
        """Test that base exception stores message."""
        error = ComfyUIError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_base_exception_is_exception(self):
        """Test that base exception inherits from Exception."""
        error = ComfyUIError("test")
        assert isinstance(error, Exception)

    def test_can_raise_and_catch(self):
        """Test that exception can be raised and caught."""
        with pytest.raises(ComfyUIError) as exc_info:
            raise ComfyUIError("test error")
        assert str(exc_info.value) == "test error"


class TestComfyUIConnectionError:
    """Test connection error exception."""

    def test_connection_error_message(self):
        """Test connection error stores message."""
        error = ComfyUIConnectionError("Failed to connect to server")
        assert str(error) == "Failed to connect to server"

    def test_connection_error_is_comfyui_error(self):
        """Test that connection error inherits from ComfyUIError."""
        error = ComfyUIConnectionError("test")
        assert isinstance(error, ComfyUIError)

    def test_can_catch_as_base_exception(self):
        """Test that connection error can be caught as base exception."""
        with pytest.raises(ComfyUIError):
            raise ComfyUIConnectionError("connection failed")


class TestComfyUIWorkflowError:
    """Test workflow error exception."""

    def test_workflow_error_message(self):
        """Test workflow error stores message."""
        error = ComfyUIWorkflowError("Invalid workflow structure")
        assert str(error) == "Invalid workflow structure"

    def test_workflow_error_is_comfyui_error(self):
        """Test that workflow error inherits from ComfyUIError."""
        error = ComfyUIWorkflowError("test")
        assert isinstance(error, ComfyUIError)

    def test_workflow_error_with_context(self):
        """Test workflow error with additional context."""
        error = ComfyUIWorkflowError(
            "Workflow validation failed",
            workflow_id="test-123",
            node_id="node-5",
        )
        assert "Workflow validation failed" in str(error)
        assert hasattr(error, "workflow_id")
        assert error.workflow_id == "test-123"
        assert error.node_id == "node-5"


class TestComfyUIQueueError:
    """Test queue error exception."""

    def test_queue_error_message(self):
        """Test queue error stores message."""
        error = ComfyUIQueueError("Queue is full")
        assert str(error) == "Queue is full"

    def test_queue_error_is_comfyui_error(self):
        """Test that queue error inherits from ComfyUIError."""
        error = ComfyUIQueueError("test")
        assert isinstance(error, ComfyUIError)

    def test_queue_error_with_prompt_id(self):
        """Test queue error with prompt ID context."""
        error = ComfyUIQueueError("Prompt not found", prompt_id="prompt-456")
        assert "Prompt not found" in str(error)
        assert hasattr(error, "prompt_id")
        assert error.prompt_id == "prompt-456"


class TestComfyUIValidationError:
    """Test validation error exception."""

    def test_validation_error_message(self):
        """Test validation error stores message."""
        error = ComfyUIValidationError("Invalid parameter")
        assert str(error) == "Invalid parameter"

    def test_validation_error_is_comfyui_error(self):
        """Test that validation error inherits from ComfyUIError."""
        error = ComfyUIValidationError("test")
        assert isinstance(error, ComfyUIError)

    def test_validation_error_with_field(self):
        """Test validation error with field context."""
        error = ComfyUIValidationError(
            "URL must start with http:// or https://",
            field="url",
            value="ftp://example.com",
        )
        assert "URL must start with http" in str(error)
        assert error.field == "url"
        assert error.value == "ftp://example.com"


class TestExceptionHierarchy:
    """Test exception hierarchy and catching."""

    def test_catch_specific_as_base(self):
        """Test that specific exceptions can be caught as base ComfyUIError."""
        exceptions = [
            ComfyUIConnectionError("conn"),
            ComfyUIWorkflowError("workflow"),
            ComfyUIQueueError("queue"),
            ComfyUIValidationError("validation"),
        ]

        for exc in exceptions:
            with pytest.raises(ComfyUIError):
                raise exc

    def test_catch_multiple_exception_types(self):
        """Test catching multiple exception types."""
        with pytest.raises((ComfyUIConnectionError, ComfyUIWorkflowError)) as exc_info:
            raise ComfyUIConnectionError("test")
        assert isinstance(exc_info.value, ComfyUIConnectionError)

        with pytest.raises((ComfyUIConnectionError, ComfyUIWorkflowError)) as exc_info:
            raise ComfyUIWorkflowError("test")
        assert isinstance(exc_info.value, ComfyUIWorkflowError)
