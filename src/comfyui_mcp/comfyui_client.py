"""ComfyUI API client with aiohttp session management.

This module provides an async HTTP client for interacting with the ComfyUI API,
managing aiohttp sessions, connection pooling, and providing proper resource cleanup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp

from comfyui_mcp.models import ComfyUIConfig

if TYPE_CHECKING:
    from types import TracebackType


class ComfyUIClient:
    """Async HTTP client for ComfyUI API with aiohttp session management.

    This client manages an aiohttp.ClientSession for making HTTP requests to the
    ComfyUI API server. It provides proper resource management through async context
    manager support and handles connection pooling, timeouts, and authentication.

    The client uses lazy session initialization - the aiohttp session is created
    when first accessed via the session property or when entering the context manager.

    Attributes:
        config: ComfyUI configuration (URL, timeout, API key, output directory)

    Example:
        >>> config = ComfyUIConfig(url="http://127.0.0.1:8188", timeout=60.0)
        >>> async with ComfyUIClient(config) as client:
        ...     # Use client for API calls
        ...     session = client.session
        ...     # Session is automatically closed on exit

        Or without context manager:
        >>> config = ComfyUIConfig(url="http://127.0.0.1:8188")
        >>> client = ComfyUIClient(config)
        >>> try:
        ...     session = client.session
        ...     # Use session for API calls
        ... finally:
        ...     await client.close()
    """

    def __init__(self, config: ComfyUIConfig) -> None:
        """Initialize the ComfyUI client with configuration.

        Args:
            config: ComfyUI configuration containing server URL, timeout,
                   optional API key, and output directory settings.

        Example:
            >>> config = ComfyUIConfig(
            ...     url="http://127.0.0.1:8188",
            ...     timeout=120.0,
            ...     api_key="optional-api-key"
            ... )
            >>> client = ComfyUIClient(config)
        """
        self.config = config
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp ClientSession.

        This property uses lazy initialization - the session is created on first
        access. The session is configured with the timeout and headers (including
        Authorization if an API key is provided) from the client's config.

        Returns:
            The aiohttp ClientSession instance for making HTTP requests.

        Example:
            >>> client = ComfyUIClient(config)
            >>> session = client.session  # Session created on first access
            >>> session2 = client.session  # Same session instance reused
            >>> assert session is session2
        """
        if self._session is None:
            # Create timeout configuration
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            # Create headers with optional API key
            headers: dict[str, str] = {}
            if self.config.api_key is not None:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            # Create session with configuration
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)

        return self._session

    async def close(self) -> None:
        """Close the aiohttp session and clean up resources.

        This method safely closes the aiohttp session if it exists. It's safe to
        call multiple times - subsequent calls are no-ops if the session is already
        closed or was never created.

        Example:
            >>> client = ComfyUIClient(config)
            >>> session = client.session
            >>> await client.close()  # Closes the session
            >>> await client.close()  # Safe to call again
        """
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> ComfyUIClient:
        """Enter the async context manager.

        This creates the aiohttp session by accessing the session property,
        ensuring the client is ready for use within the context.

        Returns:
            The client instance itself.

        Example:
            >>> async with ComfyUIClient(config) as client:
            ...     # client.session is ready for use
            ...     pass
        """
        # Accessing session property ensures it's created
        _ = self.session
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context manager and close the session.

        This ensures the aiohttp session is properly closed when exiting the
        context, even if an exception occurred.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised

        Example:
            >>> async with ComfyUIClient(config) as client:
            ...     raise ValueError("Error")  # Session still gets closed
        """
        await self.close()


__all__ = ["ComfyUIClient"]
