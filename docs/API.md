# ComfyUI MCP Server API Reference

Comprehensive API documentation for all public methods, classes, and functions in the ComfyUI MCP Server package.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
  - [ComfyUIClient](#comfyuiclient)
  - [ComfyUIConfig](#comfyuiconfig)
- [Data Models](#data-models)
  - [WorkflowNode](#workflownode)
  - [WorkflowPrompt](#workflowprompt)
  - [WorkflowTemplate](#workflowtemplate)
  - [GenerationRequest](#generationrequest)
  - [GenerationResult](#generationresult)
  - [WorkflowStatus](#workflowstatus)
  - [WorkflowState](#workflowstate)
  - [TemplateParameter](#templateparameter)
- [Utilities](#utilities)
  - [retry_with_backoff](#retry_with_backoff)
- [Exceptions](#exceptions)
- [Type Hints](#type-hints)
- [Examples](#examples)

---

## Installation

```bash
pip install comfyui-mcp
```

Or install from source:

```bash
git clone https://github.com/PurlieuStudios/comfyui-mcp.git
cd comfyui-mcp
pip install -e .
```

---

## Quick Start

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

async def main():
    # Configure the client
    config = ComfyUIConfig(url="http://localhost:8188")

    # Create client instance
    async with ComfyUIClient(config) as client:
        # Check server health
        is_healthy = await client.health_check()
        print(f"Server healthy: {is_healthy}")

asyncio.run(main())
```

---

## Core Classes

### ComfyUIClient

The main client class for interacting with a ComfyUI server.

#### Constructor

```python
ComfyUIClient(config: ComfyUIConfig)
```

**Parameters:**
- `config` (`ComfyUIConfig`): Configuration object containing server URL, API key, timeout, and output directory settings.

**Example:**

```python
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

config = ComfyUIConfig(
    url="http://localhost:8188",
    api_key="your-api-key",  # Optional
    timeout=120.0,
    output_dir="/path/to/output"  # Optional
)

async with ComfyUIClient(config) as client:
    # Use the client
    pass
```

#### Methods

##### `async health_check() -> bool`

Check if the ComfyUI server is healthy and responsive.

**Returns:**
- `bool`: `True` if the server is healthy, `False` otherwise.

**Raises:**
- `ComfyUIConnectionError`: If the server cannot be reached.
- `ComfyUITimeoutError`: If the health check times out.

**Example:**

```python
async with ComfyUIClient(config) as client:
    if await client.health_check():
        print("Server is healthy")
    else:
        print("Server is unhealthy")
```

---

##### `async submit_workflow(workflow: WorkflowPrompt) -> str`

Submit a workflow to the ComfyUI server for execution.

**Parameters:**
- `workflow` (`WorkflowPrompt`): The workflow prompt containing nodes and configuration.

**Returns:**
- `str`: Prompt ID for tracking the workflow execution.

**Raises:**
- `ComfyUIConnectionError`: If submission fails due to connection issues.
- `ComfyUIAPIError`: If the API returns an error response.
- `WorkflowValidationError`: If the workflow is invalid.

**Example:**

```python
from comfyui_mcp import WorkflowPrompt, WorkflowNode

workflow = WorkflowPrompt(
    nodes={
        "1": WorkflowNode(
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "model.safetensors"}
        ),
        "2": WorkflowNode(
            class_type="KSampler",
            inputs={
                "seed": 42,
                "steps": 20,
                "model": ["1", 0]
            }
        )
    }
)

async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)
    print(f"Workflow submitted: {prompt_id}")
```

---

##### `async get_queue_status() -> dict[str, Any]`

Get the current queue status from the ComfyUI server.

**Returns:**
- `dict[str, Any]`: Queue status containing pending and running workflows.

**Example:**

```python
async with ComfyUIClient(config) as client:
    status = await client.get_queue_status()
    print(f"Pending: {len(status['queue_pending'])}")
    print(f"Running: {len(status['queue_running'])}")
```

---

##### `async get_history(prompt_id: str) -> dict[str, Any]`

Retrieve the execution history for a specific workflow.

**Parameters:**
- `prompt_id` (`str`): The prompt ID returned from `submit_workflow()`.

**Returns:**
- `dict[str, Any]`: Execution history including outputs, status, and metadata.

**Raises:**
- `ComfyUINotFoundError`: If the prompt ID doesn't exist.

**Example:**

```python
async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)

    # Wait for completion
    await asyncio.sleep(10)

    history = await client.get_history(prompt_id)
    print(f"Status: {history[prompt_id]['status']}")
```

---

##### `async download_image(filename: str, subfolder: str = "", folder_type: str = "output") -> bytes`

Download a generated image from the ComfyUI server.

**Parameters:**
- `filename` (`str`): Name of the image file to download.
- `subfolder` (`str`, optional): Subfolder path within the output directory. Default: `""`.
- `folder_type` (`str`, optional): Type of folder (`"output"`, `"input"`, `"temp"`). Default: `"output"`.

**Returns:**
- `bytes`: Raw image data.

**Raises:**
- `ComfyUINotFoundError`: If the image file doesn't exist.
- `ComfyUIConnectionError`: If download fails.

**Example:**

```python
async with ComfyUIClient(config) as client:
    image_data = await client.download_image("generated_image.png")

    with open("output.png", "wb") as f:
        f.write(image_data)
```

---

##### `async cancel_workflow(prompt_id: str) -> bool`

Cancel a pending or running workflow.

**Parameters:**
- `prompt_id` (`str`): The prompt ID of the workflow to cancel.

**Returns:**
- `bool`: `True` if cancellation was successful, `False` otherwise.

**Raises:**
- `ComfyUINotFoundError`: If the prompt ID doesn't exist.

**Example:**

```python
async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)

    # Cancel the workflow
    cancelled = await client.cancel_workflow(prompt_id)
    print(f"Cancelled: {cancelled}")
```

---

##### `async wait_for_completion(prompt_id: str, poll_interval: float = 1.0, timeout: float | None = None) -> dict[str, Any]`

Wait for a workflow to complete execution.

**Parameters:**
- `prompt_id` (`str`): The prompt ID to wait for.
- `poll_interval` (`float`, optional): Time in seconds between status checks. Default: `1.0`.
- `timeout` (`float | None`, optional): Maximum time to wait in seconds. `None` for no timeout. Default: `None`.

**Returns:**
- `dict[str, Any]`: Final execution history.

**Raises:**
- `ComfyUITimeoutError`: If the timeout is reached before completion.
- `WorkflowExecutionError`: If the workflow execution fails.

**Example:**

```python
async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)

    # Wait up to 5 minutes
    result = await client.wait_for_completion(
        prompt_id,
        poll_interval=2.0,
        timeout=300.0
    )

    print("Workflow completed!")
```

---

### ComfyUIConfig

Configuration model for ComfyUI server connection settings.

#### Constructor

```python
ComfyUIConfig(
    url: str,
    api_key: str | None = None,
    timeout: float = 120.0,
    output_dir: str | None = None
)
```

**Parameters:**
- `url` (`str`): ComfyUI server URL (e.g., `"http://localhost:8188"`). Must start with `http://` or `https://`.
- `api_key` (`str | None`, optional): Optional API key for authentication. Must be at least 8 characters if provided.
- `timeout` (`float`, optional): Request timeout in seconds (1.0 - 3600.0). Default: `120.0`.
- `output_dir` (`str | None`, optional): Optional directory path for saving generated images.

**Validation Rules:**
- URL trailing slashes are automatically removed
- API key must be ≥ 8 characters if provided
- Timeout must be between 1.0 and 3600.0 seconds
- Output directory must not be empty or whitespace-only if provided

**Example:**

```python
from comfyui_mcp import ComfyUIConfig

# Minimal configuration
config = ComfyUIConfig(url="http://localhost:8188")

# Full configuration
config = ComfyUIConfig(
    url="https://comfyui.example.com:8443",
    api_key="sk-my-secret-key-12345",
    timeout=60.0,
    output_dir="/var/comfyui/output"
)
```

#### Class Methods

##### `from_env() -> ComfyUIConfig`

Load configuration from environment variables.

**Environment Variables:**
- `COMFYUI_URL` (required): ComfyUI server URL
- `COMFYUI_API_KEY` (optional): API key for authentication
- `COMFYUI_TIMEOUT` (optional): Request timeout in seconds (default: 120.0)
- `COMFYUI_OUTPUT_DIR` (optional): Directory for saving generated images

**Returns:**
- `ComfyUIConfig`: Configuration instance loaded from environment.

**Raises:**
- `ValueError`: If `COMFYUI_URL` is not set or is empty.
- `ValidationError`: If any environment variable value fails validation.

**Example:**

```python
import os
from comfyui_mcp import ComfyUIConfig

# Set environment variables
os.environ["COMFYUI_URL"] = "http://localhost:8188"
os.environ["COMFYUI_TIMEOUT"] = "60.0"

# Load from environment
config = ComfyUIConfig.from_env()
```

---

## Data Models

All data models are Pydantic models with automatic validation and serialization.

### WorkflowNode

Represents a single node in a ComfyUI workflow.

**Attributes:**
- `class_type` (`str`): The type of node (e.g., `"KSampler"`, `"CheckpointLoaderSimple"`).
- `inputs` (`dict[str, Any]`): Node parameters and connections to other nodes.

**Example:**

```python
from comfyui_mcp import WorkflowNode

node = WorkflowNode(
    class_type="KSampler",
    inputs={
        "seed": 42,
        "steps": 20,
        "cfg": 7.0,
        "model": ["1", 0]  # Connection to node "1", output slot 0
    }
)
```

---

### WorkflowPrompt

Represents a complete ComfyUI workflow prompt for image generation.

**Attributes:**
- `nodes` (`dict[str, WorkflowNode]`): Dictionary mapping node IDs to WorkflowNode objects.
- `client_id` (`str | None`, optional): Optional client identifier for WebSocket progress tracking.

**Methods:**

##### `to_api_format() -> dict[str, Any]`

Convert workflow prompt to ComfyUI API `/prompt` format.

**Returns:**
- `dict[str, Any]`: Dictionary in the format expected by the ComfyUI `/prompt` endpoint.

##### `get_seed() -> int | None`

Extract the seed value from the first KSampler node.

**Returns:**
- `int | None`: The seed value, or `None` if no KSampler node exists.

##### `set_seed(seed: int) -> None`

Update the seed value in all KSampler nodes.

**Parameters:**
- `seed` (`int`): The new seed value to set.

**Example:**

```python
from comfyui_mcp import WorkflowPrompt, WorkflowNode

workflow = WorkflowPrompt(
    nodes={
        "1": WorkflowNode(
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "model.safetensors"}
        ),
        "2": WorkflowNode(
            class_type="KSampler",
            inputs={"seed": 42, "steps": 20}
        )
    },
    client_id="my-client"
)

# Get current seed
current_seed = workflow.get_seed()  # 42

# Update seed
workflow.set_seed(999)

# Convert to API format
api_data = workflow.to_api_format()
```

---

### WorkflowTemplate

Represents a reusable ComfyUI workflow template.

**Attributes:**
- `name` (`str`): Template name.
- `description` (`str`): Description of what the template generates.
- `category` (`str | None`, optional): Template category (e.g., `"character"`, `"item"`, `"environment"`).
- `parameters` (`dict[str, TemplateParameter]`): Parameter definitions.
- `nodes` (`dict[str, WorkflowNode]`): Base workflow structure with parameter placeholders.

**Methods:**

##### `instantiate(params: dict[str, Any] | None = None) -> WorkflowPrompt`

Create a WorkflowPrompt instance from this template by substituting parameters.

**Parameters:**
- `params` (`dict[str, Any] | None`, optional): Parameter values to substitute. Uses defaults if not provided.

**Returns:**
- `WorkflowPrompt`: Workflow instance with all placeholders replaced.

**Example:**

```python
from comfyui_mcp import WorkflowTemplate, TemplateParameter, WorkflowNode

template = WorkflowTemplate(
    name="Character Portrait Generator",
    description="Generate character portraits for RPG games",
    category="character",
    parameters={
        "prompt": TemplateParameter(
            name="prompt",
            description="Character description",
            type="string",
            default="a warrior in armor",
            required=True
        ),
        "seed": TemplateParameter(
            name="seed",
            description="Random seed",
            type="int",
            default=42,
            required=False
        )
    },
    nodes={
        "1": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={"text": "{{prompt}}"}
        ),
        "2": WorkflowNode(
            class_type="KSampler",
            inputs={"seed": "{{seed}}", "steps": 20}
        )
    }
)

# Instantiate with custom parameters
workflow = template.instantiate({
    "prompt": "an elven mage with staff",
    "seed": 123
})
```

---

### GenerationRequest

Represents a request to generate images using a workflow template.

**Attributes:**
- `template_id` (`str`): Identifier of the workflow template to use.
- `params` (`dict[str, Any]`, optional): Parameters to substitute in the template. Default: `{}`.
- `output_settings` (`dict[str, Any]`, optional): Output configuration (directory, format, etc.). Default: `{}`.

**Example:**

```python
from comfyui_mcp import GenerationRequest

request = GenerationRequest(
    template_id="character-portrait",
    params={
        "prompt": "a warrior in armor",
        "seed": 42,
        "steps": 20
    },
    output_settings={
        "output_dir": "/game/assets/characters",
        "format": "png"
    }
)
```

---

### GenerationResult

Represents the result of a ComfyUI image generation operation.

**Attributes:**
- `images` (`list[str]`): List of file paths to generated images.
- `execution_time` (`float`): Time taken for generation in seconds.
- `metadata` (`dict[str, Any]`, optional): Generation metadata (model, dimensions, parameters). Default: `{}`.
- `prompt_id` (`str | None`, optional): ComfyUI prompt ID for tracking.
- `seed` (`int | None`, optional): Seed value used for generation.

**Example:**

```python
from comfyui_mcp import GenerationResult

result = GenerationResult(
    images=["output/character_001.png"],
    execution_time=8.5,
    metadata={
        "model": "v1-5-pruned.safetensors",
        "steps": 20,
        "width": 512,
        "height": 512
    },
    prompt_id="prompt-abc123",
    seed=42
)

print(f"Generated {len(result.images)} images in {result.execution_time}s")
```

---

### WorkflowStatus

Represents the current execution status of a workflow.

**Attributes:**
- `state` (`WorkflowState`): Current execution state.
- `queue_position` (`int | None`, optional): Position in execution queue (`None` if not queued). Default: `None`.
- `progress` (`float`, optional): Execution progress from 0.0 to 1.0. Default: `0.0`.

**Example:**

```python
from comfyui_mcp import WorkflowStatus, WorkflowState

status = WorkflowStatus(
    state=WorkflowState.RUNNING,
    queue_position=None,
    progress=0.67
)

print(f"Status: {status.state}")
print(f"Progress: {status.progress * 100:.0f}%")
```

---

### WorkflowState

Enumeration of possible workflow execution states.

**Values:**
- `PENDING`: Workflow has been created but not yet submitted
- `QUEUED`: Workflow is waiting in the execution queue
- `RUNNING`: Workflow is currently being executed
- `COMPLETED`: Workflow execution finished successfully
- `FAILED`: Workflow execution failed with an error
- `CANCELLED`: Workflow execution was cancelled by user

**Example:**

```python
from comfyui_mcp import WorkflowState, WorkflowStatus

status = WorkflowStatus(state=WorkflowState.RUNNING, progress=0.5)

if status.state == WorkflowState.COMPLETED:
    print("Workflow finished!")
elif status.state == WorkflowState.FAILED:
    print("Workflow failed!")
elif status.state == WorkflowState.RUNNING:
    print(f"Workflow running: {status.progress * 100:.0f}%")
```

---

### TemplateParameter

Represents a parameter definition for a workflow template.

**Attributes:**
- `name` (`str`): Parameter name.
- `description` (`str`): Human-readable description of the parameter.
- `type` (`str`): Parameter type (`"string"`, `"int"`, `"float"`, `"bool"`).
- `default` (`Any`): Default value for the parameter.
- `required` (`bool`, optional): Whether the parameter must be provided. Default: `True`.

**Example:**

```python
from comfyui_mcp import TemplateParameter

param = TemplateParameter(
    name="steps",
    description="Number of sampling steps",
    type="int",
    default=20,
    required=False
)
```

---

## Utilities

### retry_with_backoff

Decorator for retrying async functions with exponential backoff.

```python
retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
)
```

**Parameters:**
- `max_retries` (`int`, optional): Maximum number of retry attempts. Default: `3`.
- `initial_delay` (`float`, optional): Initial delay in seconds before first retry. Default: `1.0`.
- `exponential_base` (`float`, optional): Base for exponential backoff calculation. Default: `2.0`.
- `max_delay` (`float`, optional): Maximum delay between retries in seconds. Default: `60.0`.
- `exceptions` (`tuple[type[Exception], ...]`, optional): Tuple of exception types to retry. Default: `(Exception,)`.

**Returns:**
- Decorated async function with retry logic.

**Example:**

```python
from comfyui_mcp import retry_with_backoff
from comfyui_mcp.exceptions import ComfyUIConnectionError
import aiohttp

@retry_with_backoff(
    max_retries=5,
    initial_delay=2.0,
    exceptions=(aiohttp.ClientError, ComfyUIConnectionError)
)
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Will retry up to 5 times with exponential backoff if connection fails
data = await fetch_data("http://api.example.com/data")
```

---

## Exceptions

All exceptions are defined in `comfyui_mcp.exceptions`.

### Exception Hierarchy

```
ComfyUIError (base)
├── ComfyUIConnectionError
├── ComfyUITimeoutError
├── ComfyUIAPIError
├── ComfyUINotFoundError
├── WorkflowValidationError
└── WorkflowExecutionError
```

### Exception Details

#### `ComfyUIError`

Base exception for all ComfyUI MCP errors.

**Attributes:**
- `message` (`str`): Error message.
- `details` (`dict[str, Any] | None`): Optional additional error details.

---

#### `ComfyUIConnectionError`

Raised when connection to the ComfyUI server fails.

**Example:**

```python
from comfyui_mcp import ComfyUIClient, ComfyUIConfig
from comfyui_mcp.exceptions import ComfyUIConnectionError

config = ComfyUIConfig(url="http://invalid:8188")

try:
    async with ComfyUIClient(config) as client:
        await client.health_check()
except ComfyUIConnectionError as e:
    print(f"Connection failed: {e.message}")
```

---

#### `ComfyUITimeoutError`

Raised when a request to the ComfyUI server times out.

---

#### `ComfyUIAPIError`

Raised when the ComfyUI API returns an error response.

**Attributes:**
- `status_code` (`int | None`): HTTP status code if available.

---

#### `ComfyUINotFoundError`

Raised when a requested resource (prompt, image, etc.) is not found.

---

#### `WorkflowValidationError`

Raised when a workflow fails validation.

---

#### `WorkflowExecutionError`

Raised when a workflow execution fails.

---

## Type Hints

All public functions and methods include full type hints. Import types from `typing` or use Python 3.10+ built-in generics:

```python
from typing import Any
from comfyui_mcp import WorkflowPrompt, WorkflowNode

async def create_workflow() -> WorkflowPrompt:
    nodes: dict[str, WorkflowNode] = {
        "1": WorkflowNode(
            class_type="KSampler",
            inputs={"seed": 42}
        )
    }
    return WorkflowPrompt(nodes=nodes)
```

---

## Examples

### Complete Generation Workflow

```python
import asyncio
from comfyui_mcp import (
    ComfyUIClient,
    ComfyUIConfig,
    WorkflowPrompt,
    WorkflowNode,
)

async def generate_character_portrait():
    # Configure client
    config = ComfyUIConfig(url="http://localhost:8188")

    # Create workflow
    workflow = WorkflowPrompt(
        nodes={
            "1": WorkflowNode(
                class_type="CheckpointLoaderSimple",
                inputs={"ckpt_name": "v1-5-pruned.safetensors"}
            ),
            "2": WorkflowNode(
                class_type="CLIPTextEncode",
                inputs={
                    "text": "a warrior in armor, detailed, high quality",
                    "clip": ["1", 1]
                }
            ),
            "3": WorkflowNode(
                class_type="KSampler",
                inputs={
                    "seed": 42,
                    "steps": 20,
                    "cfg": 7.0,
                    "model": ["1", 0],
                    "positive": ["2", 0]
                }
            ),
            "4": WorkflowNode(
                class_type="SaveImage",
                inputs={
                    "images": ["3", 0],
                    "filename_prefix": "character"
                }
            )
        }
    )

    # Submit and wait
    async with ComfyUIClient(config) as client:
        # Submit workflow
        prompt_id = await client.submit_workflow(workflow)
        print(f"Submitted workflow: {prompt_id}")

        # Wait for completion
        result = await client.wait_for_completion(
            prompt_id,
            poll_interval=2.0,
            timeout=300.0
        )

        print("Generation complete!")
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(generate_character_portrait())
```

### Using Environment Variables

```python
import os
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

# Set environment variables
os.environ["COMFYUI_URL"] = "http://localhost:8188"
os.environ["COMFYUI_TIMEOUT"] = "60.0"
os.environ["COMFYUI_OUTPUT_DIR"] = "/path/to/output"

async def main():
    # Load config from environment
    config = ComfyUIConfig.from_env()

    async with ComfyUIClient(config) as client:
        is_healthy = await client.health_check()
        print(f"Server healthy: {is_healthy}")

asyncio.run(main())
```

### Error Handling

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig, WorkflowPrompt
from comfyui_mcp.exceptions import (
    ComfyUIConnectionError,
    ComfyUITimeoutError,
    WorkflowExecutionError,
)

async def safe_generation(workflow: WorkflowPrompt):
    config = ComfyUIConfig(url="http://localhost:8188")

    try:
        async with ComfyUIClient(config) as client:
            prompt_id = await client.submit_workflow(workflow)
            result = await client.wait_for_completion(
                prompt_id,
                timeout=300.0
            )
            return result

    except ComfyUIConnectionError as e:
        print(f"Connection failed: {e.message}")
        return None

    except ComfyUITimeoutError as e:
        print(f"Timeout: {e.message}")
        return None

    except WorkflowExecutionError as e:
        print(f"Workflow failed: {e.message}")
        if e.details:
            print(f"Details: {e.details}")
        return None
```

### Batch Processing

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig, WorkflowPrompt

async def batch_generate(workflows: list[WorkflowPrompt]):
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        # Submit all workflows
        prompt_ids = []
        for workflow in workflows:
            prompt_id = await client.submit_workflow(workflow)
            prompt_ids.append(prompt_id)
            print(f"Submitted: {prompt_id}")

        # Wait for all to complete
        results = []
        for prompt_id in prompt_ids:
            result = await client.wait_for_completion(prompt_id)
            results.append(result)
            print(f"Completed: {prompt_id}")

        return results

# Usage
workflows = [create_workflow(seed=i) for i in range(10)]
results = await batch_generate(workflows)
```

---

## See Also

- [ComfyUI API Integration Patterns](./docs/COMFYUI_API.md)
- [Workflow Template System](./docs/WORKFLOW_TEMPLATES.md)
- [Godot Integration Guide](./docs/GODOT_INTEGRATION.md)
- [Contributing Guide](./CONTRIBUTING.md)

---

**Version:** 0.1.0
**License:** MIT
**Repository:** https://github.com/PurlieuStudios/comfyui-mcp
