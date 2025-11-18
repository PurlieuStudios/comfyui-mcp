"""ComfyUI API client with aiohttp session management.

This module provides an async HTTP client for interacting with the ComfyUI API,
managing aiohttp sessions, connection pooling, and providing proper resource cleanup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import aiohttp

from comfyui_mcp.models import (
    ComfyUIConfig,
    GenerationResult,
    WorkflowPrompt,
    WorkflowState,
    WorkflowStatus,
)

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

    async def validate_connection(self) -> bool:
        """Validate connection to the ComfyUI server.

        This method performs a simple health check by attempting to connect to
        the ComfyUI server's /queue endpoint. It returns True if the server is
        reachable and responds successfully, False otherwise.

        Returns:
            True if connection is successful, False if server is unreachable,
            times out, or returns an error status code.

        Example:
            >>> config = ComfyUIConfig(url="http://127.0.0.1:8188")
            >>> client = ComfyUIClient(config)
            >>> is_connected = await client.validate_connection()
            >>> if is_connected:
            ...     print("ComfyUI server is reachable")
            ... else:
            ...     print("ComfyUI server is not available")
        """
        try:
            base_url = self.config.url.rstrip("/")
            url = f"{base_url}/queue"
            async with self.session.get(url) as response:
                # Consider 2xx status codes as successful connection
                status: int = response.status
                return 200 <= status < 300
        except (
            aiohttp.ClientConnectorError,
            aiohttp.ClientError,
            TimeoutError,
            Exception,
        ):
            # Any connection error means server is not reachable
            return False

    async def health_check(self, endpoint: str = "/queue") -> dict[str, Any]:
        """Perform comprehensive health check on ComfyUI server.

        This method attempts to connect to the ComfyUI server and returns
        detailed information about the connection status, including whether
        the connection succeeded, the URL checked, HTTP status code, and
        any error information if the connection failed.

        Args:
            endpoint: API endpoint to check (default: "/queue"). Can be customized
                     to check other endpoints like "/history" or "/system_stats".

        Returns:
            Dictionary containing health check results with keys:
            - connected (bool): Whether connection was successful
            - url (str): The full URL that was checked
            - status_code (int, optional): HTTP status code if connection succeeded
            - error (str, optional): Error message if connection failed

        Example:
            >>> config = ComfyUIConfig(url="http://127.0.0.1:8188")
            >>> client = ComfyUIClient(config)
            >>> health = await client.health_check()
            >>> print(health)
            {
                "connected": True,
                "url": "http://127.0.0.1:8188/queue",
                "status_code": 200
            }

            Check custom endpoint:
            >>> health = await client.health_check(endpoint="/system_stats")
        """
        base_url = self.config.url.rstrip("/")
        url = f"{base_url}{endpoint}"
        result: dict[str, Any] = {
            "connected": False,
            "url": url,
        }

        try:
            async with self.session.get(url) as response:
                result["status_code"] = response.status
                # Consider 2xx status codes as successful
                result["connected"] = 200 <= response.status < 300
        except aiohttp.ClientConnectorError as e:
            result["error"] = f"Connection failed: {e}"
        except aiohttp.ClientError as e:
            result["error"] = f"Client error: {e}"
        except TimeoutError:
            result["error"] = "Request timed out"
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"

        return result

    async def submit_workflow(self, workflow: WorkflowPrompt) -> dict[str, Any]:
        """Submit a workflow to ComfyUI for execution.

        This method submits a workflow prompt to the ComfyUI server's /prompt endpoint
        for processing. The workflow is converted to the proper API format using the
        WorkflowPrompt.to_api_format() method before submission.

        Args:
            workflow: WorkflowPrompt object containing nodes and configuration

        Returns:
            Dictionary containing the server response, which includes:
            - prompt_id (str): Unique identifier for the submitted workflow

        Raises:
            aiohttp.ClientError: If there's an HTTP error during submission
            aiohttp.ClientConnectorError: If cannot connect to server
            TimeoutError: If the request times out
            Exception: For other unexpected errors

        Example:
            >>> config = ComfyUIConfig(url="http://127.0.0.1:8188")
            >>> client = ComfyUIClient(config)
            >>> workflow = WorkflowPrompt(
            ...     nodes={
            ...         "1": WorkflowNode(
            ...             class_type="KSampler",
            ...             inputs={"seed": 123, "steps": 20}
            ...         )
            ...     }
            ... )
            >>> response = await client.submit_workflow(workflow)
            >>> print(response["prompt_id"])
            prompt-abc123

            With client_id for progress tracking:
            >>> workflow = WorkflowPrompt(
            ...     nodes={...},
            ...     client_id="my-client-id"
            ... )
            >>> response = await client.submit_workflow(workflow)
        """
        base_url = self.config.url.rstrip("/")
        url = f"{base_url}/prompt"

        # Convert workflow to ComfyUI API format
        payload = workflow.to_api_format()

        # Submit workflow via POST request
        async with self.session.post(url, json=payload) as response:
            # Raise exception for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            # Return the JSON response
            result: dict[str, Any] = await response.json()
            return result

    async def get_queue_status(self, prompt_id: str) -> WorkflowStatus:
        """Get queue status for a specific workflow by prompt ID.

        This method queries the ComfyUI /queue endpoint to determine the current
        execution state and position of a workflow in the processing queue.

        Args:
            prompt_id: The unique prompt ID returned from submit_workflow

        Returns:
            WorkflowStatus object containing:
            - state: Current workflow state (RUNNING, QUEUED, COMPLETED, etc.)
            - queue_position: Position in queue if queued (0-indexed), None otherwise
            - progress: Execution progress (0.0 for not started, 1.0 for complete)

        Raises:
            aiohttp.ClientError: If there's an HTTP error
            aiohttp.ClientConnectorError: If cannot connect to server
            TimeoutError: If the request times out
            Exception: For other unexpected errors

        Example:
            >>> config = ComfyUIConfig(url="http://127.0.0.1:8188")
            >>> client = ComfyUIClient(config)
            >>> response = await client.submit_workflow(workflow)
            >>> prompt_id = response["prompt_id"]
            >>> status = await client.get_queue_status(prompt_id)
            >>> print(f"State: {status.state}, Position: {status.queue_position}")
            State: WorkflowState.QUEUED, Position: 2
        """
        base_url = self.config.url.rstrip("/")
        url = f"{base_url}/queue"

        # Query the queue endpoint
        async with self.session.get(url) as response:
            # Raise exception for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            # Get the queue data
            queue_data: dict[str, Any] = await response.json()

        # Extract running and pending queues
        queue_running: list[list[Any]] = queue_data.get("queue_running", [])
        queue_pending: list[list[Any]] = queue_data.get("queue_pending", [])

        # Check if prompt is currently running
        for item in queue_running:
            if len(item) > 0 and item[0] == prompt_id:
                return WorkflowStatus(
                    state=WorkflowState.RUNNING,
                    queue_position=None,
                    progress=0.0,
                )

        # Check if prompt is in pending queue
        for index, item in enumerate(queue_pending):
            if len(item) > 0 and item[0] == prompt_id:
                return WorkflowStatus(
                    state=WorkflowState.QUEUED,
                    queue_position=index,
                    progress=0.0,
                )

        # If not found in either queue, assume it's completed
        return WorkflowStatus(
            state=WorkflowState.COMPLETED,
            queue_position=None,
            progress=1.0,
        )

    async def get_history(self, prompt_id: str) -> GenerationResult:
        """Get workflow execution history and results for a specific prompt ID.

        This method queries the ComfyUI /history/{prompt_id} endpoint to retrieve
        execution results including generated images, metadata, and timing information.

        Args:
            prompt_id: The unique prompt ID returned from submit_workflow

        Returns:
            GenerationResult containing:
            - images: List of generated image file paths
            - execution_time: Time taken for generation (currently 0.0)
            - metadata: Empty dict (future: workflow parameters, dimensions, etc.)
            - prompt_id: The prompt ID used for this generation
            - seed: None (future: extract from workflow if available)

        Raises:
            aiohttp.ClientError: If there's an HTTP error
            aiohttp.ClientConnectorError: If cannot connect to server
            TimeoutError: If the request times out
            ValueError: If prompt_id not found in history or no outputs available

        Example:
            >>> config = ComfyUIConfig(url="http://127.0.0.1:8188")
            >>> client = ComfyUIClient(config)
            >>> response = await client.submit_workflow(workflow)
            >>> prompt_id = response["prompt_id"]
            >>> result = await client.get_history(prompt_id)
            >>> print(f"Generated images: {result.images}")
            Generated images: ['output/image_001.png']
        """
        base_url = self.config.url.rstrip("/")
        url = f"{base_url}/history/{prompt_id}"

        # Query the history endpoint
        async with self.session.get(url) as response:
            # Raise exception for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            # Get the history data
            history_data: dict[str, Any] = await response.json()

        # Check if prompt_id exists in history
        if prompt_id not in history_data:
            raise ValueError(f"Prompt ID '{prompt_id}' not found in history")

        # Get the specific prompt history
        prompt_history: dict[str, Any] = history_data[prompt_id]

        # Extract outputs
        outputs: dict[str, Any] = prompt_history.get("outputs", {})

        if not outputs:
            raise ValueError(
                f"No outputs found for prompt ID '{prompt_id}'. "
                "Workflow may not have completed yet."
            )

        # Collect all images from all output nodes
        image_paths: list[str] = []

        for _node_id, node_output in outputs.items():
            # Check if this output node has images
            if "images" in node_output:
                images_list: list[dict[str, Any]] = node_output["images"]

                for image_info in images_list:
                    filename: str = image_info.get("filename", "")
                    subfolder: str = image_info.get("subfolder", "")

                    # Construct full path
                    if subfolder:
                        full_path = f"{subfolder}/{filename}"
                    else:
                        full_path = filename

                    if full_path:
                        image_paths.append(full_path)

        # Create and return GenerationResult
        return GenerationResult(
            images=image_paths,
            execution_time=0.0,  # TODO: Extract from history if available
            metadata={},  # TODO: Extract workflow metadata if needed
            prompt_id=prompt_id,
            seed=None,  # TODO: Extract seed from workflow if needed
        )

    async def download_image(
        self, filename: str, subfolder: str = "", image_type: str = "output"
    ) -> bytes:
        """Download a generated image from ComfyUI server.

        This method queries the ComfyUI /view endpoint to download raw image bytes.
        The image is identified by filename, optional subfolder, and type.

        Args:
            filename: The image filename (e.g., "ComfyUI_00001_.png")
            subfolder: Optional subfolder path (e.g., "2024-01", default: "")
            image_type: Type of image (default: "output", can be "temp", "input", etc.)

        Returns:
            Raw image bytes (PNG, JPEG, etc.)

        Raises:
            aiohttp.ClientError: If there's an HTTP error
            aiohttp.ClientConnectorError: If cannot connect to server
            aiohttp.ClientResponseError: If image not found (404) or server error
            TimeoutError: If the request times out

        Example:
            >>> config = ComfyUIConfig(url="http://127.0.0.1:8188")
            >>> client = ComfyUIClient(config)
            >>> # Get history first to find image filenames
            >>> result = await client.get_history("prompt-123")
            >>> # Download first image
            >>> image_data = await client.download_image(result.images[0])
            >>> # Save to file
            >>> with open("output.png", "wb") as f:
            ...     f.write(image_data)

            Download with subfolder:
            >>> image_data = await client.download_image(
            ...     "image.png",
            ...     subfolder="2024-01"
            ... )
        """
        base_url = self.config.url.rstrip("/")
        url = f"{base_url}/view"

        # Build query parameters for ComfyUI /view endpoint
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": image_type,
        }

        # Download the image
        async with self.session.get(url, params=params) as response:
            # Raise exception for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            # Read and return the raw image bytes
            image_bytes: bytes = await response.read()
            return image_bytes

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
