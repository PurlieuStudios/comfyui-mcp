"""Data models for ComfyUI workflows and prompts.

This module defines Pydantic models that represent ComfyUI workflows,
nodes, and prompts used for AI image generation.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


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


class GenerationResult(BaseModel):
    """Represents the result of a ComfyUI image generation operation.

    Contains generated images, execution metadata, and timing information.
    This model captures the complete output of a workflow execution including
    paths to generated images and associated metadata.

    Attributes:
        images: List of file paths to generated images
        execution_time: Time taken for generation in seconds
        metadata: Dictionary containing generation metadata (model, dimensions, etc.)
        prompt_id: Optional ComfyUI prompt ID for tracking this generation
        seed: Optional seed value used for generation (from KSampler nodes)

    Example:
        >>> result = GenerationResult(
        ...     images=["output/character.png"],
        ...     execution_time=8.5,
        ...     metadata={"model": "v1-5-pruned.safetensors", "steps": 20},
        ...     prompt_id="prompt-abc123",
        ...     seed=42
        ... )
    """

    images: list[str] = Field(..., description="List of generated image file paths")
    execution_time: float = Field(
        ..., description="Generation execution time in seconds"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Generation metadata (model name, dimensions, parameters, etc.)",
    )
    prompt_id: str | None = Field(
        default=None,
        description="ComfyUI prompt ID for tracking this generation",
    )
    seed: int | None = Field(
        default=None,
        description="Seed value used for generation (from KSampler nodes)",
    )

    model_config = {"extra": "forbid"}


class GenerationRequest(BaseModel):
    """Represents a request to generate images using a workflow template.

    This model encapsulates all the information needed to execute an image
    generation request, including which template to use, what parameters to
    pass to it, and how to handle the output.

    Attributes:
        template_id: Identifier of the workflow template to use
        params: Dictionary of parameters to substitute in the template
        output_settings: Configuration for output handling (directory, format, etc.)

    Example:
        >>> request = GenerationRequest(
        ...     template_id="character-portrait",
        ...     params={
        ...         "prompt": "a warrior in armor",
        ...         "seed": 42,
        ...         "steps": 20
        ...     },
        ...     output_settings={
        ...         "output_dir": "/game/assets/characters",
        ...         "format": "png"
        ...     }
        ... )
    """

    template_id: str = Field(
        ..., min_length=1, description="Workflow template identifier"
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to substitute in the template",
    )
    output_settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Output configuration (directory, format, filename, etc.)",
    )

    model_config = {"extra": "forbid"}


class ComfyUIConfig(BaseModel):
    """Configuration for connecting to a ComfyUI server.

    Contains all settings needed to connect to and interact with a ComfyUI
    instance, including server URL, authentication, timeouts, and output paths.

    Attributes:
        url: ComfyUI server URL (e.g., "http://127.0.0.1:8188")
        api_key: Optional API key for authentication (min 8 chars if provided)
        timeout: Request timeout in seconds (1.0 - 3600.0, default: 120.0)
        output_dir: Optional directory path for saving generated images

    Validation Rules:
        - URL: Must start with http:// or https://, trailing slashes removed
        - API Key: If provided, must be non-empty, non-whitespace, min 8 characters
        - Timeout: Must be between 1.0 and 3600.0 seconds (1 second to 1 hour)
        - Output Dir: If provided, must be non-empty and non-whitespace

    Example:
        >>> config = ComfyUIConfig(
        ...     url="http://127.0.0.1:8188/",  # Trailing slash removed
        ...     api_key="sk-my-secret-key-12345",  # Min 8 chars
        ...     timeout=60.0,  # Between 1.0 and 3600.0
        ...     output_dir="/game/assets/generated"
        ... )
        >>> assert config.url == "http://127.0.0.1:8188"  # No trailing slash
    """

    url: str = Field(
        ...,
        description="ComfyUI server URL",
        pattern=r"^https?://",
    )
    api_key: str | None = Field(
        default=None,
        description="Optional API key for authentication",
    )
    timeout: float = Field(
        default=120.0,
        gt=0.0,
        description="Request timeout in seconds (must be > 0)",
    )
    output_dir: str | None = Field(
        default=None,
        description="Optional directory path for saving generated images",
    )

    model_config = {"extra": "forbid", "frozen": True}

    @field_validator("url")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        """Remove trailing slashes from URL for consistency.

        Args:
            v: The URL value to validate

        Returns:
            URL with trailing slashes removed

        Example:
            >>> "http://localhost:8188///" -> "http://localhost:8188"
        """
        return v.rstrip("/")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str | None) -> str | None:
        """Validate API key if provided.

        Args:
            v: The API key value to validate

        Returns:
            The validated API key

        Raises:
            ValueError: If API key is empty, whitespace-only, or shorter than 8 characters

        Example:
            >>> validate_api_key("sk-123456789")  # Valid: >= 8 chars
            >>> validate_api_key("")  # Raises ValueError
            >>> validate_api_key("short")  # Raises ValueError: < 8 chars
        """
        if v is not None:
            # Check for empty or whitespace-only
            if not v or not v.strip():
                msg = "API key must not be empty or whitespace-only"
                raise ValueError(msg)

            # Check minimum length for security
            if len(v) < 8:
                msg = "API key must be at least 8 characters long"
                raise ValueError(msg)

        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        """Validate timeout is within reasonable bounds.

        Args:
            v: The timeout value to validate

        Returns:
            The validated timeout value

        Raises:
            ValueError: If timeout is below 1.0 or above 3600.0 seconds

        Example:
            >>> validate_timeout(60.0)  # Valid
            >>> validate_timeout(0.5)  # Raises ValueError: < 1.0
            >>> validate_timeout(7200.0)  # Raises ValueError: > 3600.0
        """
        if v < 1.0:
            msg = "Timeout must be at least 1.0 second"
            raise ValueError(msg)

        if v > 3600.0:
            msg = "Timeout must not exceed 3600.0 seconds (1 hour)"
            raise ValueError(msg)

        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: str | None) -> str | None:
        """Validate output directory if provided.

        Args:
            v: The output directory path to validate

        Returns:
            The validated output directory path

        Raises:
            ValueError: If output_dir is empty or whitespace-only

        Example:
            >>> validate_output_dir("/path/to/output")  # Valid
            >>> validate_output_dir("")  # Raises ValueError
            >>> validate_output_dir("   ")  # Raises ValueError
        """
        if v is not None:
            # Check for empty or whitespace-only
            if not v or not v.strip():
                msg = "Output directory must not be empty or whitespace-only"
                raise ValueError(msg)

        return v

    @classmethod
    def from_env(cls) -> ComfyUIConfig:
        """Load configuration from environment variables.

        Reads configuration values from the following environment variables:
        - COMFYUI_URL (required): ComfyUI server URL
        - COMFYUI_API_KEY (optional): API key for authentication
        - COMFYUI_TIMEOUT (optional): Request timeout in seconds (default: 120.0)
        - COMFYUI_OUTPUT_DIR (optional): Directory for saving generated images

        All string values are automatically trimmed of leading/trailing whitespace.
        All field validators are applied to the loaded values.

        Returns:
            ComfyUIConfig instance with values loaded from environment variables

        Raises:
            ValueError: If COMFYUI_URL is not set or is empty
            ValidationError: If any environment variable value fails validation

        Example:
            >>> import os
            >>> os.environ["COMFYUI_URL"] = "http://localhost:8188"
            >>> os.environ["COMFYUI_TIMEOUT"] = "60.0"
            >>> config = ComfyUIConfig.from_env()
            >>> assert config.url == "http://localhost:8188"
            >>> assert config.timeout == 60.0
        """
        import os

        # Required: COMFYUI_URL
        url = os.environ.get("COMFYUI_URL", "").strip()
        if not url:
            msg = "COMFYUI_URL environment variable is required"
            raise ValueError(msg)

        # Optional: COMFYUI_API_KEY
        api_key_raw = os.environ.get("COMFYUI_API_KEY")
        api_key = api_key_raw.strip() if api_key_raw is not None else None

        # Optional: COMFYUI_TIMEOUT (with type conversion)
        timeout_raw = os.environ.get("COMFYUI_TIMEOUT")
        timeout = float(timeout_raw.strip()) if timeout_raw is not None else 120.0

        # Optional: COMFYUI_OUTPUT_DIR
        output_dir_raw = os.environ.get("COMFYUI_OUTPUT_DIR")
        output_dir = output_dir_raw.strip() if output_dir_raw is not None else None

        # Create config instance (validators will run automatically)
        return cls(
            url=url,
            api_key=api_key,
            timeout=timeout,
            output_dir=output_dir,
        )

    @classmethod
    def from_file(cls, config_path: Path | str | None = None) -> ComfyUIConfig:
        """Load configuration from TOML file.

        Loads configuration from a TOML file with a [comfyui] section.
        If config_path is None, searches for configuration files in standard
        locations (current directory, user config, system config).

        Args:
            config_path: Path to TOML configuration file. If None, searches
                         standard locations in this order:
                         1. ./comfyui.toml (current directory)
                         2. ~/.config/comfyui/comfyui.toml (user config)
                         3. /etc/comfyui/comfyui.toml (system config, Unix only)

        Returns:
            ComfyUIConfig instance with values loaded from the configuration file.
            Any fields not specified in the file use their default values.

        Raises:
            FileNotFoundError: If config_path is provided but doesn't exist, or
                               if config_path is None and no config file is found
                               in standard locations.
            ValueError: If the TOML file doesn't contain a [comfyui] section.
            ValidationError: If configuration values fail validation (e.g., invalid
                             URL, timeout out of range, API key too short).

        Example:
            >>> # Load from specific file
            >>> config = ComfyUIConfig.from_file("/path/to/config.toml")
            >>> print(config.url)
            http://localhost:8188

            >>> # Load from standard locations (searches automatically)
            >>> config = ComfyUIConfig.from_file()
            >>> print(config.timeout)
            120.0
        """
        import os
        from pathlib import Path

        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib

        # Import here to avoid circular dependency
        from comfyui_mcp.config import find_config_file

        # If no path provided, search standard locations
        if config_path is None:
            config_path = find_config_file()
            if config_path is None:
                msg = (
                    "No config file found in standard locations. "
                    "Searched: ./comfyui.toml, ~/.config/comfyui/comfyui.toml"
                )
                if os.name != "nt":
                    msg += ", /etc/comfyui/comfyui.toml"
                raise FileNotFoundError(msg)

        # Convert to Path if string
        if isinstance(config_path, str):
            config_path = Path(config_path)

        # Check file exists
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)

        # Load TOML file
        with open(config_path, "rb") as f:
            toml_data = tomllib.load(f)

        # Check for [comfyui] section
        if "comfyui" not in toml_data:
            msg = f"Config file must contain [comfyui] section: {config_path}"
            raise ValueError(msg)

        config_section = toml_data["comfyui"]

        # Extract fields (use defaults if not specified)
        url = config_section.get("url")
        if url is None:
            msg = "Config file must specify 'url' in [comfyui] section"
            raise ValueError(msg)

        api_key = config_section.get("api_key")
        timeout = config_section.get("timeout", 120.0)
        output_dir = config_section.get("output_dir")

        # Create config instance (validators will run automatically)
        return cls(
            url=url,
            api_key=api_key,
            timeout=float(timeout),
            output_dir=output_dir,
        )


class WorkflowState(str, Enum):
    """Enumeration of possible workflow execution states.

    Represents the current execution state of a ComfyUI workflow in the
    processing pipeline, from initial submission through completion or failure.

    Values:
        PENDING: Workflow has been created but not yet submitted
        QUEUED: Workflow is waiting in the execution queue
        RUNNING: Workflow is currently being executed
        COMPLETED: Workflow execution finished successfully
        FAILED: Workflow execution failed with an error
        CANCELLED: Workflow execution was cancelled by user

    Example:
        >>> status = WorkflowStatus(state=WorkflowState.RUNNING, progress=0.5)
        >>> if status.state == WorkflowState.COMPLETED:
        ...     print("Workflow finished!")
    """

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(BaseModel):
    """Represents the current execution status of a workflow.

    Tracks the state, progress, and queue position of a workflow being
    processed by ComfyUI. This model is used for monitoring workflow
    execution and providing real-time status updates.

    Attributes:
        state: Current execution state (pending, queued, running, etc.)
        queue_position: Position in execution queue (None if not queued, >= 0 if queued)
        progress: Execution progress from 0.0 (not started) to 1.0 (complete)

    Example:
        >>> status = WorkflowStatus(
        ...     state=WorkflowState.RUNNING,
        ...     queue_position=None,
        ...     progress=0.67
        ... )
        >>> print(f"Workflow is {status.progress * 100:.0f}% complete")
        Workflow is 67% complete
    """

    state: WorkflowState = Field(
        ...,
        description="Current workflow execution state",
    )
    queue_position: int | None = Field(
        default=None,
        ge=0,
        description="Position in execution queue (None if not queued, >= 0 if queued)",
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Execution progress from 0.0 (not started) to 1.0 (complete)",
    )

    model_config = {"extra": "forbid"}


class TemplateParameter(BaseModel):
    """Represents a parameter definition for a workflow template.

    Template parameters define what values can be customized when instantiating
    a workflow from a template. Each parameter has a type, default value, and
    indicates whether it's required.

    Attributes:
        name: Parameter name (e.g., "prompt", "width", "seed")
        description: Human-readable description of the parameter
        type: Parameter type ("string", "int", "float", "bool")
        default: Default value for the parameter
        required: Whether the parameter must be provided (default: True)

    Example:
        >>> param = TemplateParameter(
        ...     name="steps",
        ...     description="Number of sampling steps",
        ...     type="int",
        ...     default=20
        ... )
    """

    name: str = Field(..., description="Parameter name")
    description: str = Field(..., description="Parameter description")
    type: str = Field(..., description="Parameter type (string, int, float, bool)")
    default: Any = Field(..., description="Default value for the parameter")
    required: bool = Field(default=True, description="Whether parameter is required")

    model_config = {"extra": "forbid"}


class WorkflowTemplate(BaseModel):
    """Represents a reusable ComfyUI workflow template.

    Workflow templates define reusable patterns for generating specific types
    of images (e.g., character portraits, item icons). Templates include
    parameter definitions and a base workflow structure that can be instantiated
    with specific parameter values.

    Attributes:
        name: Template name (e.g., "Character Portrait Generator")
        description: Description of what the template generates
        category: Template category (optional: "character", "item", "environment")
        parameters: Dictionary of parameter definitions
        nodes: Base workflow structure with parameter placeholders

    Example:
        >>> template = WorkflowTemplate(
        ...     name="Simple Generator",
        ...     description="Basic image generation",
        ...     parameters={
        ...         "prompt": TemplateParameter(
        ...             name="prompt",
        ...             description="Text prompt",
        ...             type="string",
        ...             default="a landscape"
        ...         )
        ...     },
        ...     nodes={
        ...         "1": WorkflowNode(
        ...             class_type="CLIPTextEncode",
        ...             inputs={"text": "{{prompt}}"}
        ...         )
        ...     }
        ... )
    """

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str | None = Field(
        default=None, description="Template category (character, item, environment)"
    )
    parameters: dict[str, TemplateParameter] = Field(
        ..., description="Parameter definitions for this template"
    )
    nodes: dict[str, WorkflowNode] = Field(
        ..., description="Base workflow structure with parameter placeholders"
    )

    model_config = {"extra": "forbid"}

    def instantiate(self, params: dict[str, Any] | None = None) -> WorkflowPrompt:
        """Create a WorkflowPrompt instance from this template.

        Substitutes parameter placeholders in the workflow nodes with actual values.
        Placeholders are in the format {{parameter_name}} and are replaced with
        values from the params dict or the parameter's default value.

        Args:
            params: Dictionary of parameter values to substitute. If a parameter
                   is not provided, its default value is used.

        Returns:
            WorkflowPrompt instance with all placeholders replaced with actual values

        Example:
            >>> template = WorkflowTemplate(...)
            >>> workflow = template.instantiate({"prompt": "a warrior", "seed": 123})
        """
        import copy

        # Start with default values
        param_values: dict[str, Any] = {}
        for param_name, param_def in self.parameters.items():
            param_values[param_name] = param_def.default

        # Override with provided values
        if params is not None:
            param_values.update(params)

        # Deep copy nodes to avoid modifying the template
        instantiated_nodes: dict[str, WorkflowNode] = {}

        for node_id, node in self.nodes.items():
            # Deep copy the node's inputs
            node_inputs = copy.deepcopy(node.inputs)

            # Substitute parameters in inputs
            node_inputs = self._substitute_parameters(node_inputs, param_values)

            # Create new node with substituted inputs
            instantiated_nodes[node_id] = WorkflowNode(
                class_type=node.class_type, inputs=node_inputs
            )

        return WorkflowPrompt(nodes=instantiated_nodes)

    def _substitute_parameters(self, obj: Any, param_values: dict[str, Any]) -> Any:
        """Recursively substitute parameter placeholders in an object.

        Args:
            obj: Object to process (can be dict, list, str, or primitive)
            param_values: Dictionary of parameter values

        Returns:
            Object with all {{parameter_name}} placeholders replaced
        """
        import re

        if isinstance(obj, str):
            # Check if the entire string is a placeholder
            match = re.fullmatch(r"\{\{(\w+)\}\}", obj)
            if match:
                param_name = match.group(1)
                value = param_values.get(param_name)
                if value is not None:
                    return value  # Return actual value, preserving type
                return obj  # Keep placeholder if no value

            # Otherwise, do string substitution
            def replacer(match: re.Match[str]) -> str:
                param_name = match.group(1)
                value = param_values.get(param_name)
                if value is None:
                    return match.group(0)  # Keep placeholder if no value
                return str(value)

            return re.sub(r"\{\{(\w+)\}\}", replacer, obj)

        elif isinstance(obj, dict):
            return {
                key: self._substitute_parameters(val, param_values)
                for key, val in obj.items()
            }

        elif isinstance(obj, list):
            return [self._substitute_parameters(item, param_values) for item in obj]

        else:
            # Return primitives as-is
            return obj

    def to_file(self, file_path: Path | str) -> None:
        """Save workflow template to JSON file.

        Serializes the workflow template to a JSON file with proper formatting.
        The JSON format includes all template metadata, parameters, and nodes.

        Args:
            file_path: Path where the JSON file should be saved. If file exists,
                      it will be overwritten.

        Example:
            >>> template = WorkflowTemplate(...)
            >>> template.to_file("workflows/my-template.json")
        """
        import json

        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Convert to dict format for JSON serialization
        data = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": {
                param_name: {
                    "name": param.name,
                    "description": param.description,
                    "type": param.type,
                    "default": param.default,
                    "required": param.required,
                }
                for param_name, param in self.parameters.items()
            },
            "nodes": {
                node_id: {"class_type": node.class_type, "inputs": node.inputs}
                for node_id, node in self.nodes.items()
            },
        }

        # Write with pretty printing (indent=2)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def from_file(cls, file_path: Path | str) -> WorkflowTemplate:
        """Load workflow template from JSON file.

        Reads and deserializes a workflow template from a JSON file.
        The JSON file must contain all required fields (name, description,
        parameters, nodes).

        Args:
            file_path: Path to the JSON template file to load

        Returns:
            WorkflowTemplate instance loaded from the JSON file

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
            ValidationError: If the JSON data doesn't match the template schema

        Example:
            >>> template = WorkflowTemplate.from_file("workflows/character-portrait.json")
            >>> print(template.name)
            Character Portrait Generator
        """
        import json

        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            msg = f"Template file not found: {file_path}"
            raise FileNotFoundError(msg)

        with open(file_path) as f:
            data = json.load(f)

        # Convert parameters from dict format to TemplateParameter objects
        parameters = {}
        for param_name, param_data in data.get("parameters", {}).items():
            parameters[param_name] = TemplateParameter(**param_data)

        # Convert nodes from dict format to WorkflowNode objects
        nodes = {}
        for node_id, node_data in data.get("nodes", {}).items():
            nodes[node_id] = WorkflowNode(**node_data)

        # Create and return WorkflowTemplate instance
        return cls(
            name=data["name"],
            description=data["description"],
            category=data.get("category"),
            parameters=parameters,
            nodes=nodes,
        )


__all__ = [
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
