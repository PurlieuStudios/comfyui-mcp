"""Image generation orchestration for ComfyUI workflows.

This module provides the ImageGenerator class which coordinates workflow template
instantiation, submission to ComfyUI, and result retrieval. It serves as the main
entry point for generating images from workflow templates.

Example:
    >>> from comfyui_mcp import ComfyUIClient, ComfyUIConfig
    >>> from comfyui_mcp.image_generator import ImageGenerator
    >>> from comfyui_mcp.template_manager import WorkflowTemplateManager
    >>>
    >>> config = ComfyUIConfig(url="http://localhost:8188")
    >>> client = ComfyUIClient(config)
    >>> manager = WorkflowTemplateManager("./workflows")
    >>> generator = ImageGenerator(client=client, template_manager=manager)
    >>>
    >>> # Generate from template
    >>> result = await generator.generate_from_template(
    ...     template_id="character-portrait",
    ...     parameters={"prompt": "a warrior", "seed": 42}
    ... )
    >>> print(f"Generated images: {result.images}")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from comfyui_mcp.comfyui_client import ComfyUIClient
    from comfyui_mcp.models import GenerationResult, WorkflowPrompt
    from comfyui_mcp.template_manager import WorkflowTemplateManager


class ImageGenerator:
    """Orchestrates image generation from workflow templates.

    The ImageGenerator class coordinates the workflow generation process by:
    1. Loading workflow templates from the template manager
    2. Instantiating templates with user-provided parameters
    3. Submitting workflows to ComfyUI via the client
    4. Retrieving and returning generation results

    This class provides the main high-level API for image generation, handling
    all the coordination between templates, workflows, and the ComfyUI backend.

    Attributes:
        client: ComfyUI API client for workflow submission and monitoring
        template_manager: Manager for loading and managing workflow templates
                         (optional - can generate from direct WorkflowPrompt)

    Example:
        >>> # With template manager
        >>> generator = ImageGenerator(client=client, template_manager=manager)
        >>> result = await generator.generate_from_template(
        ...     template_id="character-portrait",
        ...     parameters={"prompt": "a wizard"}
        ... )
        >>>
        >>> # Without template manager (direct workflow)
        >>> generator = ImageGenerator(client=client)
        >>> result = await generator.generate(workflow=my_workflow)
    """

    def __init__(
        self,
        client: ComfyUIClient,
        template_manager: WorkflowTemplateManager | None = None,
    ) -> None:
        """Initialize the ImageGenerator.

        Args:
            client: ComfyUI API client for workflow submission and result retrieval
            template_manager: Optional template manager for loading workflow templates.
                            If not provided, only direct workflow generation is supported.

        Example:
            >>> config = ComfyUIConfig(url="http://localhost:8188")
            >>> client = ComfyUIClient(config)
            >>> manager = WorkflowTemplateManager("./workflows")
            >>> generator = ImageGenerator(client=client, template_manager=manager)
        """
        self.client = client
        self.template_manager = template_manager

    async def generate_from_template(
        self,
        template_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """Generate images from a workflow template.

        Loads the specified template, instantiates it with the provided parameters,
        submits the workflow to ComfyUI, and retrieves the generation result.

        Args:
            template_id: ID (filename without extension) of the template to use
            parameters: Parameter values to substitute into the template.
                       If not provided, template defaults are used.

        Returns:
            GenerationResult containing generated images, metadata, and timing info

        Raises:
            ValueError: If no template_manager is configured
            FileNotFoundError: If the specified template does not exist
            ValidationError: If required template parameters are missing or invalid
            ComfyUIError: If workflow submission or execution fails

        Example:
            >>> result = await generator.generate_from_template(
            ...     template_id="character-portrait",
            ...     parameters={
            ...         "prompt": "a mighty warrior",
            ...         "seed": 12345,
            ...         "width": 512,
            ...         "height": 768
            ...     }
            ... )
            >>> print(f"Generated {len(result.images)} images")
            >>> print(f"Execution time: {result.execution_time}s")
        """
        if self.template_manager is None:
            msg = (
                "Cannot generate from template: no template_manager configured. "
                "Provide a WorkflowTemplateManager during initialization or use "
                "generate() with a direct WorkflowPrompt."
            )
            raise ValueError(msg)

        # Load the template
        template = self.template_manager.load_template(template_id)

        # Instantiate the template with parameters
        workflow = template.instantiate(parameters or {})

        # Generate using the instantiated workflow
        return await self.generate(workflow=workflow)

    async def generate(
        self,
        workflow: WorkflowPrompt,
    ) -> GenerationResult:
        """Generate images from a workflow prompt.

        Submits the workflow to ComfyUI and retrieves the generation result.
        This method provides direct workflow execution without template instantiation.

        Args:
            workflow: WorkflowPrompt containing the complete workflow definition

        Returns:
            GenerationResult containing generated images, metadata, and timing info

        Raises:
            ComfyUIError: If workflow submission or execution fails

        Example:
            >>> from comfyui_mcp import WorkflowPrompt, WorkflowNode
            >>>
            >>> workflow = WorkflowPrompt(
            ...     prompt={
            ...         "1": WorkflowNode(
            ...             class_type="CLIPTextEncode",
            ...             inputs={"text": "a warrior"}
            ...         ),
            ...         # ... more nodes
            ...     }
            ... )
            >>> result = await generator.generate(workflow=workflow)
        """
        # Submit workflow to ComfyUI
        response = await self.client.submit_workflow(workflow)

        # Extract prompt ID from response
        prompt_id: str = response["prompt_id"]

        # Retrieve generation result from history
        result: GenerationResult = await self.client.get_history(prompt_id)

        return result
