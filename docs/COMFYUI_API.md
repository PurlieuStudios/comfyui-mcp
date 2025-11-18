# ComfyUI API Integration Patterns

Comprehensive guide to integrating with the ComfyUI API for workflow-based image generation.

## Table of Contents

- [Overview](#overview)
- [API Endpoints](#api-endpoints)
- [Workflow Structure](#workflow-structure)
- [Integration Patterns](#integration-patterns)
- [Queue Management](#queue-management)
- [WebSocket Real-Time Updates](#websocket-real-time-updates)
- [Image Retrieval](#image-retrieval)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)

---

## Overview

ComfyUI provides a REST API for submitting and monitoring workflow-based image generation tasks. The ComfyUI MCP Server wraps this API with a Python client (`ComfyUIClient`) that provides typed, async methods for all operations.

### Architecture

```
┌─────────────────┐
│  Your App/Game  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ ComfyUIClient   │  ← Python client (comfyui_mcp)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  ComfyUI REST   │  ← HTTP REST API + WebSocket
│      API        │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  ComfyUI        │  ← Image generation engine
│   Server        │
└─────────────────┘
```

### Base URL

Default ComfyUI server runs on:
```
http://127.0.0.1:8188
```

All endpoints are relative to this base URL.

---

## API Endpoints

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/prompt` | POST | Submit workflow for execution |
| `/queue` | GET | Get current queue status |
| `/history` | GET | Get execution history |
| `/history/{prompt_id}` | GET | Get specific workflow result |
| `/view` | GET | Download generated images |
| `/interrupt` | POST | Cancel running workflow |
| `/ws` | WebSocket | Real-time progress updates |

---

### POST /prompt

Submit a workflow prompt for execution.

**Request Body:**

```json
{
  "prompt": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "v1-5-pruned.safetensors"
      }
    },
    "2": {
      "class_type": "KSampler",
      "inputs": {
        "seed": 42,
        "steps": 20,
        "cfg": 7.0,
        "model": ["1", 0]
      }
    }
  },
  "client_id": "optional-client-identifier"
}
```

**Response:**

```json
{
  "prompt_id": "abc123-def456-789",
  "number": 42,
  "node_errors": {}
}
```

**Fields:**
- `prompt_id`: Unique identifier for tracking this workflow
- `number`: Queue position number
- `node_errors`: Object containing any validation errors per node

**Python Example:**

```python
from comfyui_mcp import ComfyUIClient, ComfyUIConfig, WorkflowPrompt, WorkflowNode

config = ComfyUIConfig(url="http://localhost:8188")

workflow = WorkflowPrompt(
    nodes={
        "1": WorkflowNode(
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "v1-5-pruned.safetensors"}
        ),
        "2": WorkflowNode(
            class_type="KSampler",
            inputs={"seed": 42, "steps": 20}
        )
    }
)

async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)
    print(f"Submitted: {prompt_id}")
```

---

### GET /queue

Get the current execution queue status.

**Response:**

```json
{
  "queue_running": [
    [42, "prompt-id-running", {"prompt": {...}}]
  ],
  "queue_pending": [
    [43, "prompt-id-pending-1", {"prompt": {...}}],
    [44, "prompt-id-pending-2", {"prompt": {...}}]
  ]
}
```

**Fields:**
- `queue_running`: Array of currently executing workflows
- `queue_pending`: Array of workflows waiting to execute
- Each entry: `[queue_number, prompt_id, workflow_data]`

**Python Example:**

```python
async with ComfyUIClient(config) as client:
    status = await client.get_queue_status()

    running = status.get("queue_running", [])
    pending = status.get("queue_pending", [])

    print(f"Running: {len(running)}")
    print(f"Pending: {len(pending)}")
```

---

### GET /history

Get execution history for all or specific workflows.

**Query Parameters:**
- `prompt_id` (optional): Filter by specific prompt ID
- `max_items` (optional): Limit number of results

**Response:**

```json
{
  "prompt-id-abc123": {
    "prompt": [42, "prompt-id-abc123", {"prompt": {...}}],
    "outputs": {
      "9": {
        "images": [
          {
            "filename": "ComfyUI_00001_.png",
            "subfolder": "",
            "type": "output"
          }
        ]
      }
    },
    "status": {
      "status_str": "success",
      "completed": true,
      "messages": [
        ["execution_start", {"prompt_id": "abc123"}],
        ["execution_cached", {"nodes": ["1", "2"]}],
        ["executing", {"node": "3"}],
        ["executed", {"node": "3", "output": {...}}]
      ]
    }
  }
}
```

**Python Example:**

```python
async with ComfyUIClient(config) as client:
    # Submit workflow
    prompt_id = await client.submit_workflow(workflow)

    # Wait a bit for execution
    await asyncio.sleep(5)

    # Get history
    history = await client.get_history(prompt_id)

    if prompt_id in history:
        result = history[prompt_id]
        status = result["status"]["status_str"]
        outputs = result.get("outputs", {})

        print(f"Status: {status}")
        print(f"Outputs: {outputs}")
```

---

### GET /view

Download a generated image file.

**Query Parameters:**
- `filename` (required): Name of the image file
- `subfolder` (optional): Subfolder path (default: "")
- `type` (optional): Folder type - "output", "input", or "temp" (default: "output")

**Response:** Binary image data (PNG, JPEG, etc.)

**Python Example:**

```python
async with ComfyUIClient(config) as client:
    # Get history to find generated image filename
    history = await client.get_history(prompt_id)
    outputs = history[prompt_id]["outputs"]

    # Find SaveImage node output
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            for image in node_output["images"]:
                filename = image["filename"]
                subfolder = image.get("subfolder", "")

                # Download image
                image_data = await client.download_image(
                    filename=filename,
                    subfolder=subfolder
                )

                # Save locally
                with open(f"output_{filename}", "wb") as f:
                    f.write(image_data)
```

---

### POST /interrupt

Cancel the currently running workflow.

**Request Body:** Empty or `{}`

**Response:**

```json
{
  "status": "interrupted"
}
```

**Python Example:**

```python
async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)

    # Cancel after 2 seconds
    await asyncio.sleep(2)
    cancelled = await client.cancel_workflow(prompt_id)

    print(f"Cancelled: {cancelled}")
```

---

## Workflow Structure

### Node-Based Architecture

ComfyUI workflows are directed acyclic graphs (DAGs) where:
- **Nodes** represent operations (loading models, sampling, saving)
- **Connections** pass data between nodes via `[node_id, output_slot]` references

### Workflow JSON Format

```json
{
  "node_id": {
    "class_type": "NodeClassName",
    "inputs": {
      "param1": "value",
      "param2": ["source_node_id", output_slot_index]
    }
  }
}
```

### Common Node Types

| Node Class | Purpose | Key Inputs |
|------------|---------|------------|
| `CheckpointLoaderSimple` | Load model checkpoint | `ckpt_name` |
| `CLIPTextEncode` | Encode text prompt | `text`, `clip` |
| `KSampler` | Generate image | `seed`, `steps`, `cfg`, `model`, `positive` |
| `VAEDecode` | Decode latent to image | `samples`, `vae` |
| `SaveImage` | Save generated image | `images`, `filename_prefix` |
| `LoadImage` | Load input image | `image` |
| `ControlNetApply` | Apply ControlNet | `conditioning`, `control_net`, `image` |

### Complete Workflow Example

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "v1-5-pruned.safetensors"
    }
  },
  "2": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "a warrior in armor, detailed, 8k",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "blurry, low quality",
      "clip": ["1", 1]
    }
  },
  "4": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 42,
      "steps": 20,
      "cfg": 7.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0]
    }
  },
  "5": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["4", 0],
      "vae": ["1", 2]
    }
  },
  "6": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": ["5", 0]
    }
  }
}
```

**Data Flow:**
1. Node 1 loads model → outputs [model, clip, vae]
2. Node 2 encodes positive prompt using CLIP from node 1
3. Node 3 encodes negative prompt using CLIP from node 1
4. Node 4 generates latent image using model and prompts
5. Node 5 decodes latent to image using VAE from node 1
6. Node 6 saves the final image

---

## Integration Patterns

### Pattern 1: Submit and Wait

Basic pattern for synchronous-style workflow execution.

```python
async def generate_and_wait(workflow: WorkflowPrompt) -> dict:
    """Submit workflow and wait for completion."""
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        # Submit workflow
        prompt_id = await client.submit_workflow(workflow)

        # Wait for completion with timeout
        result = await client.wait_for_completion(
            prompt_id=prompt_id,
            poll_interval=1.0,  # Check every 1 second
            timeout=300.0        # 5 minute timeout
        )

        return result
```

**Use Cases:**
- Simple one-off generation
- CLI tools
- Testing and debugging

---

### Pattern 2: Submit and Poll

Submit workflow and manually poll for completion.

```python
async def generate_with_polling(workflow: WorkflowPrompt) -> dict:
    """Submit workflow and manually poll for completion."""
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        prompt_id = await client.submit_workflow(workflow)

        # Poll until complete
        while True:
            history = await client.get_history(prompt_id)

            if prompt_id in history:
                status = history[prompt_id]["status"]
                if status.get("completed", False):
                    return history[prompt_id]

            await asyncio.sleep(1.0)
```

**Use Cases:**
- Custom progress tracking
- Advanced error handling
- Integration with existing event loops

---

### Pattern 3: Batch Submission

Submit multiple workflows in parallel.

```python
async def batch_generate(workflows: list[WorkflowPrompt]) -> list[dict]:
    """Submit multiple workflows and wait for all to complete."""
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        # Submit all workflows
        prompt_ids = []
        for workflow in workflows:
            prompt_id = await client.submit_workflow(workflow)
            prompt_ids.append(prompt_id)

        # Wait for all to complete
        results = []
        for prompt_id in prompt_ids:
            result = await client.wait_for_completion(prompt_id)
            results.append(result)

        return results
```

**Use Cases:**
- Batch processing
- Generating variations
- High-throughput applications

---

### Pattern 4: Queue Management

Monitor and manage the execution queue.

```python
async def manage_queue():
    """Monitor queue and cancel old workflows."""
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        while True:
            status = await client.get_queue_status()

            # Check pending queue
            pending = status.get("queue_pending", [])

            # Cancel workflows older than 5 minutes
            current_time = time.time()
            for queue_num, prompt_id, data in pending:
                # Check age (you'd track submission time separately)
                if should_cancel(prompt_id):
                    await client.cancel_workflow(prompt_id)
                    print(f"Cancelled old workflow: {prompt_id}")

            await asyncio.sleep(10)
```

**Use Cases:**
- Resource management
- Timeout enforcement
- Priority queue implementation

---

### Pattern 5: WebSocket Real-Time Updates

Listen for real-time workflow progress via WebSocket.

```python
import websockets
import json

async def monitor_workflow_progress(prompt_id: str):
    """Monitor workflow execution via WebSocket."""
    ws_url = "ws://localhost:8188/ws?clientId=my-client"

    async with websockets.connect(ws_url) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            msg_type = data.get("type")

            if msg_type == "executing":
                node = data["data"]["node"]
                print(f"Executing node: {node}")

            elif msg_type == "executed":
                node = data["data"]["node"]
                output = data["data"]["output"]
                print(f"Completed node: {node}")

            elif msg_type == "execution_complete":
                print("Workflow complete!")
                break
```

**Use Cases:**
- Progress bars
- Real-time UI updates
- Streaming results

---

## Queue Management

### Queue States

ComfyUI maintains two queues:
1. **Running Queue**: Currently executing workflows (usually 1)
2. **Pending Queue**: Workflows waiting to execute

### Queue Operations

**Get Queue Status:**
```python
status = await client.get_queue_status()
running_count = len(status["queue_running"])
pending_count = len(status["queue_pending"])
```

**Cancel Workflow:**
```python
# Cancel by prompt ID
cancelled = await client.cancel_workflow(prompt_id)
```

**Clear Entire Queue:**
```python
# Get all pending workflows
status = await client.get_queue_status()
for _, prompt_id, _ in status["queue_pending"]:
    await client.cancel_workflow(prompt_id)
```

### Queue Best Practices

1. **Monitor Queue Depth**: Don't let pending queue grow too large
2. **Implement Timeouts**: Cancel workflows that take too long
3. **Priority Management**: Cancel low-priority workflows when high-priority ones arrive
4. **Rate Limiting**: Limit workflow submissions to prevent queue overflow

---

## WebSocket Real-Time Updates

### Connection

Connect to WebSocket endpoint with client ID:
```
ws://localhost:8188/ws?clientId=my-unique-client-id
```

### Message Types

| Type | Description | Data Fields |
|------|-------------|-------------|
| `status` | Queue status update | `status`, `sid` |
| `executing` | Node started executing | `node`, `prompt_id` |
| `executed` | Node finished executing | `node`, `output`, `prompt_id` |
| `execution_start` | Workflow execution started | `prompt_id` |
| `execution_cached` | Nodes loaded from cache | `nodes`, `prompt_id` |
| `execution_error` | Execution error occurred | `prompt_id`, `node_id`, `exception_message` |
| `execution_complete` | Workflow completed | `prompt_id` |

### Example WebSocket Messages

**Execution Start:**
```json
{
  "type": "execution_start",
  "data": {
    "prompt_id": "abc123"
  }
}
```

**Node Executing:**
```json
{
  "type": "executing",
  "data": {
    "node": "4",
    "prompt_id": "abc123"
  }
}
```

**Node Executed:**
```json
{
  "type": "executed",
  "data": {
    "node": "4",
    "output": {
      "images": [...]
    },
    "prompt_id": "abc123"
  }
}
```

**Execution Complete:**
```json
{
  "type": "execution_complete",
  "data": {
    "prompt_id": "abc123"
  }
}
```

---

## Image Retrieval

### Finding Generated Images

After workflow completion, get image information from history:

```python
history = await client.get_history(prompt_id)
workflow_result = history[prompt_id]

# Find SaveImage node outputs
for node_id, output in workflow_result["outputs"].items():
    if "images" in output:
        for image_info in output["images"]:
            filename = image_info["filename"]
            subfolder = image_info.get("subfolder", "")
            image_type = image_info.get("type", "output")

            # Download image
            image_data = await client.download_image(
                filename=filename,
                subfolder=subfolder,
                folder_type=image_type
            )
```

### Image Storage Locations

ComfyUI stores images in different folders:
- **output**: Generated images (default)
- **input**: Uploaded input images
- **temp**: Temporary files

### Image Formats

ComfyUI supports:
- PNG (default, lossless)
- JPEG (lossy, smaller files)
- WebP (modern, efficient)

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check workflow structure |
| 404 | Not Found | Prompt ID doesn't exist |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Server overloaded, retry later |

### Common Errors

**Node Validation Errors:**
```json
{
  "error": {
    "type": "prompt_error",
    "message": "Invalid node",
    "details": "Node '5' input 'model' does not exist",
    "extra_info": {...}
  }
}
```

**Missing Model Error:**
```json
{
  "node_errors": {
    "1": {
      "errors": [{
        "type": "value_not_in_list",
        "message": "Checkpoint 'nonexistent.safetensors' not found"
      }],
      "class_type": "CheckpointLoaderSimple"
    }
  }
}
```

### Error Handling Pattern

```python
from comfyui_mcp.exceptions import (
    ComfyUIConnectionError,
    ComfyUIAPIError,
    WorkflowValidationError,
)

async def safe_generate(workflow: WorkflowPrompt):
    """Generate with comprehensive error handling."""
    config = ComfyUIConfig(url="http://localhost:8188")

    try:
        async with ComfyUIClient(config) as client:
            # Check server health first
            if not await client.health_check():
                raise ComfyUIConnectionError("Server unhealthy")

            # Submit workflow
            prompt_id = await client.submit_workflow(workflow)

            # Wait for completion
            result = await client.wait_for_completion(
                prompt_id,
                timeout=300.0
            )

            return result

    except ComfyUIConnectionError as e:
        print(f"Connection failed: {e.message}")
        # Maybe retry or switch to backup server

    except WorkflowValidationError as e:
        print(f"Invalid workflow: {e.message}")
        if e.details:
            print(f"Details: {e.details}")
        # Fix workflow structure

    except ComfyUIAPIError as e:
        print(f"API error: {e.message}")
        # Handle specific API errors

    except Exception as e:
        print(f"Unexpected error: {e}")
        # Log and alert
```

---

## Best Practices

### 1. Use Health Checks

Always verify server availability before submitting workflows:

```python
async with ComfyUIClient(config) as client:
    if not await client.health_check():
        raise Exception("ComfyUI server not available")

    # Proceed with workflow submission
    prompt_id = await client.submit_workflow(workflow)
```

### 2. Implement Retry Logic

Use exponential backoff for transient failures:

```python
from comfyui_mcp import retry_with_backoff
from comfyui_mcp.exceptions import ComfyUIConnectionError

@retry_with_backoff(
    max_retries=3,
    initial_delay=1.0,
    exponential_base=2.0,
    exceptions=(ComfyUIConnectionError,)
)
async def submit_with_retry(workflow: WorkflowPrompt) -> str:
    async with ComfyUIClient(config) as client:
        return await client.submit_workflow(workflow)
```

### 3. Set Appropriate Timeouts

Configure timeouts based on expected generation time:

```python
# Fast generations (simple workflows)
config = ComfyUIConfig(url="...", timeout=30.0)

# Complex generations (many steps, high resolution)
config = ComfyUIConfig(url="...", timeout=300.0)

# Background processing
config = ComfyUIConfig(url="...", timeout=3600.0)
```

### 4. Clean Up Resources

Always use async context managers:

```python
# Good: Automatic cleanup
async with ComfyUIClient(config) as client:
    await client.submit_workflow(workflow)

# Avoid: Manual session management
client = ComfyUIClient(config)
try:
    await client.submit_workflow(workflow)
finally:
    await client.close()
```

### 5. Monitor Queue Depth

Prevent queue overflow:

```python
async def submit_if_capacity(workflow: WorkflowPrompt, max_pending: int = 10):
    """Only submit if queue has capacity."""
    async with ComfyUIClient(config) as client:
        status = await client.get_queue_status()
        pending_count = len(status["queue_pending"])

        if pending_count >= max_pending:
            raise Exception(f"Queue full: {pending_count} workflows pending")

        return await client.submit_workflow(workflow)
```

### 6. Validate Workflows Before Submission

Check workflow structure:

```python
def validate_workflow(workflow: WorkflowPrompt) -> bool:
    """Validate workflow has required nodes."""
    nodes = workflow.nodes

    # Check for required node types
    has_checkpoint = any(
        n.class_type == "CheckpointLoaderSimple"
        for n in nodes.values()
    )
    has_sampler = any(
        n.class_type == "KSampler"
        for n in nodes.values()
    )

    if not has_checkpoint:
        raise WorkflowValidationError("Missing CheckpointLoaderSimple node")
    if not has_sampler:
        raise WorkflowValidationError("Missing KSampler node")

    return True
```

### 7. Use Descriptive Client IDs

When using WebSocket, use meaningful client IDs:

```python
# Good: Descriptive ID
workflow = WorkflowPrompt(
    nodes=nodes,
    client_id="game-client-player123-portrait"
)

# Avoid: Generic ID
workflow = WorkflowPrompt(
    nodes=nodes,
    client_id="client1"
)
```

---

## Common Patterns

### Pattern: Generate Variations

Generate multiple variations of the same prompt with different seeds:

```python
async def generate_variations(
    base_workflow: WorkflowPrompt,
    count: int = 4
) -> list[dict]:
    """Generate multiple variations with different seeds."""
    variations = []

    for i in range(count):
        # Clone workflow and update seed
        workflow = copy.deepcopy(base_workflow)
        workflow.set_seed(random.randint(0, 2**32 - 1))

        # Submit and wait
        async with ComfyUIClient(config) as client:
            prompt_id = await client.submit_workflow(workflow)
            result = await client.wait_for_completion(prompt_id)
            variations.append(result)

    return variations
```

### Pattern: Progressive Quality

Generate low quality first, then upscale:

```python
async def generate_progressive(prompt: str):
    """Generate at low res, then upscale."""
    # First: Quick 512x512 generation
    low_res_workflow = create_workflow(prompt, width=512, height=512, steps=15)

    async with ComfyUIClient(config) as client:
        prompt_id = await client.submit_workflow(low_res_workflow)
        low_res_result = await client.wait_for_completion(prompt_id)

        # Get low-res image
        low_res_image = extract_image(low_res_result)

        # Second: Upscale to 1024x1024
        upscale_workflow = create_upscale_workflow(low_res_image)
        prompt_id = await client.submit_workflow(upscale_workflow)
        high_res_result = await client.wait_for_completion(prompt_id)

        return high_res_result
```

### Pattern: Caching Results

Cache generated images to avoid regeneration:

```python
import hashlib
import json

cache = {}

async def generate_with_cache(workflow: WorkflowPrompt) -> dict:
    """Generate with result caching."""
    # Create cache key from workflow
    workflow_json = json.dumps(workflow.to_api_format(), sort_keys=True)
    cache_key = hashlib.sha256(workflow_json.encode()).hexdigest()

    # Check cache
    if cache_key in cache:
        print(f"Cache hit: {cache_key}")
        return cache[cache_key]

    # Generate
    async with ComfyUIClient(config) as client:
        prompt_id = await client.submit_workflow(workflow)
        result = await client.wait_for_completion(prompt_id)

    # Store in cache
    cache[cache_key] = result
    return result
```

### Pattern: Parallel Generation

Generate multiple images in parallel:

```python
async def parallel_generate(workflows: list[WorkflowPrompt]) -> list[dict]:
    """Generate multiple workflows concurrently."""
    async def generate_one(workflow: WorkflowPrompt) -> dict:
        async with ComfyUIClient(config) as client:
            prompt_id = await client.submit_workflow(workflow)
            return await client.wait_for_completion(prompt_id)

    # Execute all workflows concurrently
    results = await asyncio.gather(
        *[generate_one(w) for w in workflows],
        return_exceptions=True
    )

    return results
```

---

## See Also

- [API Reference](./API.md) - Complete Python API documentation
- [Workflow Templates](./WORKFLOW_TEMPLATES.md) - Reusable workflow templates
- [Godot Integration](./GODOT_INTEGRATION.md) - Godot game engine integration
- [Contributing](../CONTRIBUTING.md) - Contributing to the project

---

**Version:** 0.1.0
**License:** MIT
**Repository:** https://github.com/PurlieuStudios/comfyui-mcp
