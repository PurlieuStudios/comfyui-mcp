"""Data models for ComfyUI workflows and prompts.

This module defines Pydantic models that represent ComfyUI workflows,
nodes, and prompts used for AI image generation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    """Represents a single node in a ComfyUI workflow.

    Each node corresponds to a processing step in the image generation pipeline,
    such as loading a model, encoding text, or sampling.

    Attributes:
        class_type: The type of node (e.g., "KSampler", "CheckpointLoaderSimple")
        inputs: Dictionary of node parameters and connections to other nodes.
                Values can be primitives (int, float, str, bool) or connections
                represented as [node_id, output_slot].

    Example:
        >>> node = WorkflowNode(
        ...     class_type="KSampler",
        ...     inputs={
        ...         "seed": 123456,
        ...         "steps": 20,
        ...         "model": ["4", 0]  # Connection to node "4", output slot 0
        ...     }
        ... )
    """

    class_type: str = Field(..., description="Type/class of the ComfyUI node")
    inputs: dict[str, Any] = Field(
        ..., description="Node parameters and connections to other nodes"
    )

    model_config = {"extra": "forbid"}


class WorkflowPrompt(BaseModel):
    """Represents a complete ComfyUI workflow prompt for image generation.

    A workflow prompt contains all nodes and their configurations needed to
    generate images via the ComfyUI API. This corresponds to the data sent
    to the POST /prompt endpoint.

    Attributes:
        nodes: Dictionary mapping node IDs (strings) to WorkflowNode objects
        client_id: Optional client identifier for WebSocket progress tracking

    Example:
        >>> prompt = WorkflowPrompt(
        ...     nodes={
        ...         "1": WorkflowNode(
        ...             class_type="CheckpointLoaderSimple",
        ...             inputs={"ckpt_name": "model.safetensors"}
        ...         ),
        ...         "2": WorkflowNode(
        ...             class_type="KSampler",
        ...             inputs={"seed": 123, "model": ["1", 0]}
        ...         )
        ...     },
        ...     client_id="my-client"
        ... )
    """

    nodes: dict[str, WorkflowNode] = Field(
        ..., description="Dictionary of node IDs to WorkflowNode objects"
    )
    client_id: str | None = Field(
        default=None, description="Optional client ID for WebSocket tracking"
    )

    model_config = {"extra": "forbid"}

    def to_api_format(self) -> dict[str, Any]:
        """Convert workflow prompt to ComfyUI API /prompt format.

        Returns:
            Dictionary in the format expected by the ComfyUI /prompt endpoint:
            {
                "prompt": {node_id: {class_type, inputs}, ...},
                "client_id": "optional_client_id"
            }

        Example:
            >>> prompt = WorkflowPrompt(nodes={"1": WorkflowNode(...)})
            >>> api_data = prompt.to_api_format()
            >>> # POST to http://comfyui:8188/prompt with api_data
        """
        # Convert nodes dict to the format ComfyUI expects
        prompt_dict: dict[str, Any] = {}
        for node_id, node in self.nodes.items():
            prompt_dict[node_id] = {
                "class_type": node.class_type,
                "inputs": node.inputs,
            }

        result: dict[str, Any] = {"prompt": prompt_dict}

        if self.client_id is not None:
            result["client_id"] = self.client_id

        return result

    def get_seed(self) -> int | None:
        """Extract the seed value from the first KSampler node.

        Searches through all nodes to find a KSampler and returns its seed value.
        This is useful for tracking or reproducing generations.

        Returns:
            The seed value from the first KSampler node found, or None if no
            KSampler node exists or if it doesn't have a seed.

        Example:
            >>> prompt = WorkflowPrompt(nodes={
            ...     "3": WorkflowNode(
            ...         class_type="KSampler",
            ...         inputs={"seed": 42}
            ...     )
            ... })
            >>> prompt.get_seed()
            42
        """
        for node in self.nodes.values():
            if node.class_type == "KSampler" and "seed" in node.inputs:
                seed_value = node.inputs["seed"]
                if isinstance(seed_value, int):
                    return seed_value
        return None

    def set_seed(self, seed: int) -> None:
        """Update the seed value in all KSampler nodes.

        This allows changing the random seed for all sampling operations
        in the workflow, which affects the generated images.

        Args:
            seed: The new seed value to set

        Example:
            >>> prompt = WorkflowPrompt(nodes={...})
            >>> prompt.set_seed(999)  # Update all KSampler nodes to use seed 999
        """
        for node in self.nodes.values():
            if node.class_type == "KSampler" and "seed" in node.inputs:
                node.inputs["seed"] = seed


__all__ = ["WorkflowNode", "WorkflowPrompt"]
