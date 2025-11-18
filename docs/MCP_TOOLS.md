# MCP Tool Usage Guide

Complete reference for using ComfyUI MCP Server tools via the Model Context Protocol.

## Table of Contents

- [Overview](#overview)
- [What is MCP?](#what-is-mcp)
- [Setup and Configuration](#setup-and-configuration)
- [Available Tools](#available-tools)
  - [generate_image](#generate_image)
  - [list_workflows](#list_workflows)
  - [get_workflow_status](#get_workflow_status)
  - [cancel_workflow](#cancel_workflow)
  - [load_workflow](#load_workflow)
- [Integration Patterns](#integration-patterns)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

---

## Overview

The ComfyUI MCP Server exposes ComfyUI's workflow-based image generation capabilities as standardized **Model Context Protocol (MCP) tools**. This allows any MCP-compatible client (such as Claude Code, custom applications, or Godot games) to generate AI images programmatically.

### Key Benefits

- **Standardized Interface**: Use the same tools across different MCP clients
- **Async Operations**: Non-blocking workflow execution
- **Template System**: Pre-built workflows for common use cases
- **Progress Tracking**: Real-time status updates
- **Error Handling**: Comprehensive error reporting

### Prerequisites

- ComfyUI installed and running (`http://localhost:8188`)
- ComfyUI MCP Server configured in `.mcp.json`
- Stable Diffusion models downloaded in ComfyUI
- MCP-compatible client (Claude Code, custom app, etc.)

---

## What is MCP?

The **Model Context Protocol (MCP)** is a universal standard for AI model integration created by Anthropic. It provides:

- **Tools**: Functions that AI assistants can call to perform actions
- **Resources**: Data sources that assistants can access
- **Prompts**: Pre-defined prompt templates for common tasks

### How MCP Works

```
┌─────────────┐         ┌──────────────┐         ┌──────────┐
│ MCP Client  │  <───>  │ MCP Server   │  <───>  │ ComfyUI  │
│ (Claude/App)│  Tools  │ (This Server)│  API    │  Server  │
└─────────────┘         └──────────────┘         └──────────┘
```

1. **Client** (e.g., Claude Code) calls an MCP tool
2. **MCP Server** (ComfyUI MCP) processes the request
3. **ComfyUI** executes the workflow and generates images
4. **MCP Server** returns results to the client

---

## Setup and Configuration

### 1. Configure MCP Server

Create or update `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "comfyui-mcp": {
      "command": "python",
      "args": ["-m", "comfyui_mcp.server"],
      "env": {
        "COMFYUI_URL": "http://localhost:8188",
        "COMFYUI_API_KEY": "your-api-key-optional",
        "COMFYUI_TIMEOUT": "120.0",
        "COMFYUI_OUTPUT_DIR": "./generated_images"
      }
    }
  }
}
```

### 2. Start the MCP Server

The MCP server starts automatically when accessed by an MCP client. You can also start it manually:

```bash
# Via Python module
python -m comfyui_mcp.server

# With custom configuration
COMFYUI_URL="http://localhost:8188" python -m comfyui_mcp.server
```

### 3. Verify ComfyUI Connection

Ensure ComfyUI is running and accessible:

```bash
# Test ComfyUI connection
curl http://localhost:8188/system_stats

# Expected response: JSON with system information
```

---

## Available Tools

### `generate_image`

Generate images using pre-built workflow templates or custom workflows.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `template` | string | Yes* | - | Workflow template name (e.g., `character-portrait`) |
| `prompt` | string | Yes | - | Text description of the image to generate |
| `negative_prompt` | string | No | `""` | Text describing what to avoid in the image |
| `width` | integer | No | `512` | Image width in pixels (multiple of 8) |
| `height` | integer | No | `512` | Image height in pixels (multiple of 8) |
| `steps` | integer | No | `20` | Number of sampling steps (1-150) |
| `cfg_scale` | float | No | `7.0` | Classifier-free guidance scale (1.0-30.0) |
| `seed` | integer | No | `random` | Random seed for reproducibility (-1 for random) |
| `sampler` | string | No | `"euler"` | Sampling method (euler, dpm++, etc.) |
| `scheduler` | string | No | `"normal"` | Scheduler type (normal, karras, exponential) |
| `denoise` | float | No | `1.0` | Denoising strength (0.0-1.0) |
| `batch_size` | integer | No | `1` | Number of images to generate (1-4) |

**Note**: Either `template` or a custom workflow must be provided.

#### Response

```json
{
  "prompt_id": "abc-123-def-456",
  "status": "queued",
  "images": [],
  "execution_time": 0.0,
  "metadata": {
    "seed": 42,
    "width": 512,
    "height": 512,
    "steps": 20,
    "cfg_scale": 7.0
  }
}
```

#### Example Usage

**Via Claude Code:**

```
Please use the generate_image tool to create a fantasy elf warrior portrait with the following parameters:
- Template: character-portrait
- Prompt: "fantasy elf warrior, detailed armor, glowing sword, heroic pose"
- Negative prompt: "blurry, low quality, deformed"
- Width: 512
- Height: 768
- Steps: 30
- Seed: 12345
```

**Via MCP Client (Python):**

```python
result = await mcp_client.call_tool(
    "generate_image",
    {
        "template": "character-portrait",
        "prompt": "fantasy elf warrior, detailed armor, glowing sword",
        "negative_prompt": "blurry, low quality",
        "width": 512,
        "height": 768,
        "steps": 30,
        "cfg_scale": 7.5,
        "seed": 12345
    }
)

print(f"Workflow ID: {result['prompt_id']}")
```

**Via JSON-RPC:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "generate_image",
    "arguments": {
      "template": "character-portrait",
      "prompt": "cyberpunk hacker, neon lights, detailed face",
      "width": 512,
      "height": 512,
      "steps": 25,
      "seed": 42
    }
  }
}
```

#### Templates Available

| Template | Description | Default Size | Best For |
|----------|-------------|--------------|----------|
| `character-portrait` | Character portraits and avatars | 512x512 | RPG characters, NPCs |
| `item-icon` | Centered item icons | 512x512 | Inventory items, UI |
| `environment-texture` | Tileable environment textures | 1024x1024 | Backgrounds, terrain |
| `pixel-art` | Upscaled pixel art style | 256x256 | Retro games, sprites |

#### Common Parameters

**Quality Settings:**
```json
{
  "steps": 30,
  "cfg_scale": 7.5,
  "sampler": "dpm_2_ancestral",
  "scheduler": "karras"
}
```

**Fast Generation (Preview):**
```json
{
  "steps": 15,
  "cfg_scale": 6.0,
  "width": 512,
  "height": 512
}
```

**High Quality:**
```json
{
  "steps": 50,
  "cfg_scale": 8.0,
  "width": 1024,
  "height": 1024,
  "sampler": "dpm_2_ancestral",
  "scheduler": "karras"
}
```

---

### `list_workflows`

List all available workflow templates.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | string | No | `null` | Filter by category (e.g., `"characters"`, `"environments"`) |
| `tags` | array[string] | No | `[]` | Filter by tags |

#### Response

```json
{
  "workflows": [
    {
      "id": "character-portrait",
      "name": "Character Portrait",
      "description": "Generate character portraits for RPGs",
      "category": "characters",
      "tags": ["portrait", "character", "rpg"],
      "default_width": 512,
      "default_height": 512,
      "parameters": [
        {
          "name": "prompt",
          "type": "string",
          "required": true,
          "description": "Character description"
        },
        {
          "name": "steps",
          "type": "integer",
          "required": false,
          "default": 20,
          "min": 1,
          "max": 150
        }
      ]
    },
    {
      "id": "item-icon",
      "name": "Item Icon",
      "description": "Generate centered item icons",
      "category": "items",
      "tags": ["icon", "item", "ui"],
      "default_width": 512,
      "default_height": 512
    }
  ],
  "total_count": 2
}
```

#### Example Usage

**Via Claude Code:**

```
Please use the list_workflows tool to show me all available workflow templates.
```

**Via MCP Client (Python):**

```python
result = await mcp_client.call_tool("list_workflows")

for workflow in result['workflows']:
    print(f"{workflow['id']}: {workflow['description']}")
```

**Filter by Category:**

```python
result = await mcp_client.call_tool(
    "list_workflows",
    {"category": "characters"}
)
```

**Filter by Tags:**

```python
result = await mcp_client.call_tool(
    "list_workflows",
    {"tags": ["portrait", "rpg"]}
)
```

---

### `get_workflow_status`

Check the status and progress of a running or completed workflow.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt_id` | string | Yes | - | The workflow prompt ID returned from `generate_image` |

#### Response

```json
{
  "prompt_id": "abc-123-def-456",
  "state": "completed",
  "progress": 1.0,
  "queue_position": 0,
  "execution_time": 45.2,
  "images": [
    {
      "filename": "ComfyUI_00001_.png",
      "subfolder": "",
      "type": "output"
    }
  ],
  "metadata": {
    "seed": 42,
    "steps": 20,
    "cfg_scale": 7.0
  }
}
```

#### Workflow States

| State | Description |
|-------|-------------|
| `queued` | Waiting in queue to be processed |
| `running` | Currently being executed |
| `completed` | Successfully completed |
| `failed` | Execution failed (check `error` field) |
| `cancelled` | Cancelled by user request |

#### Example Usage

**Via Claude Code:**

```
Please check the status of workflow abc-123-def-456 using the get_workflow_status tool.
```

**Via MCP Client (Python):**

```python
result = await mcp_client.call_tool(
    "get_workflow_status",
    {"prompt_id": "abc-123-def-456"}
)

print(f"Status: {result['state']}")
print(f"Progress: {result['progress'] * 100}%")

if result['state'] == 'completed':
    print(f"Generated {len(result['images'])} image(s)")
    print(f"Execution time: {result['execution_time']:.2f}s")
```

**Polling Example:**

```python
import asyncio

async def wait_for_completion(prompt_id: str, poll_interval: float = 2.0):
    """Poll workflow status until completion."""
    while True:
        result = await mcp_client.call_tool(
            "get_workflow_status",
            {"prompt_id": prompt_id}
        )

        state = result['state']
        progress = result['progress']

        print(f"Status: {state} ({progress * 100:.1f}%)")

        if state in ['completed', 'failed', 'cancelled']:
            return result

        await asyncio.sleep(poll_interval)

# Usage
result = await wait_for_completion("abc-123-def-456")
```

---

### `cancel_workflow`

Cancel a queued or running workflow.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt_id` | string | No | `null` | Specific workflow to cancel |
| `interrupt` | boolean | No | `false` | Interrupt currently running workflow |

**Note**: If `prompt_id` is not provided, `interrupt` must be `true` to cancel the currently running workflow.

#### Response

```json
{
  "cancelled": true,
  "prompt_id": "abc-123-def-456",
  "message": "Workflow cancelled successfully"
}
```

#### Example Usage

**Via Claude Code:**

```
Please cancel workflow abc-123-def-456 using the cancel_workflow tool.
```

**Via MCP Client (Python):**

**Cancel Specific Workflow:**

```python
result = await mcp_client.call_tool(
    "cancel_workflow",
    {"prompt_id": "abc-123-def-456"}
)

print(result['message'])
```

**Interrupt Current Workflow:**

```python
result = await mcp_client.call_tool(
    "cancel_workflow",
    {"interrupt": True}
)

print("Current workflow interrupted")
```

**Cancel Multiple Workflows:**

```python
prompt_ids = ["abc-123", "def-456", "ghi-789"]

for prompt_id in prompt_ids:
    result = await mcp_client.call_tool(
        "cancel_workflow",
        {"prompt_id": prompt_id}
    )
    print(f"Cancelled {prompt_id}")
```

---

### `load_workflow`

Load and execute a custom workflow from a JSON file.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `workflow_path` | string | Yes | - | Path to workflow JSON file (absolute or relative) |
| `parameters` | object | No | `{}` | Parameter overrides for the workflow |

#### Response

```json
{
  "prompt_id": "abc-123-def-456",
  "status": "queued",
  "workflow_name": "custom_workflow.json",
  "parameters_applied": {
    "seed": 12345,
    "steps": 30
  }
}
```

#### Example Usage

**Via Claude Code:**

```
Please load the workflow from ./workflows/my_custom_workflow.json and execute it with seed 42.
```

**Via MCP Client (Python):**

```python
result = await mcp_client.call_tool(
    "load_workflow",
    {
        "workflow_path": "./workflows/custom_character.json",
        "parameters": {
            "seed": 42,
            "steps": 30,
            "cfg_scale": 7.5
        }
    }
)

prompt_id = result['prompt_id']
print(f"Custom workflow started: {prompt_id}")
```

**Load and Monitor:**

```python
# Load workflow
result = await mcp_client.call_tool(
    "load_workflow",
    {"workflow_path": "./workflows/upscale_4x.json"}
)

prompt_id = result['prompt_id']

# Wait for completion
final_result = await wait_for_completion(prompt_id)
```

#### Custom Workflow Format

Workflows must be valid ComfyUI JSON format:

```json
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 42,
      "steps": 20,
      "cfg": 7.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["5", 0]
    }
  },
  "4": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "sd_v1-5.safetensors"
    }
  }
}
```

---

## Integration Patterns

### Pattern 1: Simple Generation

Generate a single image and wait for completion.

```python
async def simple_generation():
    # Generate image
    result = await mcp_client.call_tool(
        "generate_image",
        {
            "template": "character-portrait",
            "prompt": "fantasy wizard with blue robes",
            "seed": 12345
        }
    )

    prompt_id = result['prompt_id']

    # Poll for completion
    while True:
        status = await mcp_client.call_tool(
            "get_workflow_status",
            {"prompt_id": prompt_id}
        )

        if status['state'] == 'completed':
            return status['images']
        elif status['state'] == 'failed':
            raise Exception(f"Generation failed: {status.get('error')}")

        await asyncio.sleep(2.0)
```

### Pattern 2: Batch Generation

Generate multiple variations of the same prompt.

```python
async def batch_generation(prompt: str, count: int = 4):
    """Generate multiple variations."""
    tasks = []

    for i in range(count):
        # Use different seeds for variations
        task = mcp_client.call_tool(
            "generate_image",
            {
                "template": "item-icon",
                "prompt": prompt,
                "seed": -1  # Random seed
            }
        )
        tasks.append(task)

    # Submit all in parallel
    results = await asyncio.gather(*tasks)

    # Collect prompt IDs
    prompt_ids = [r['prompt_id'] for r in results]

    # Wait for all to complete
    final_results = await asyncio.gather(*[
        wait_for_completion(pid) for pid in prompt_ids
    ])

    return final_results
```

### Pattern 3: Template Discovery

List and select appropriate workflow templates.

```python
async def find_template(category: str = None, tags: list = None):
    """Find appropriate workflow template."""
    result = await mcp_client.call_tool(
        "list_workflows",
        {
            "category": category,
            "tags": tags
        }
    )

    workflows = result['workflows']

    if not workflows:
        return None

    # Return first matching template
    return workflows[0]['id']

# Usage
template_id = await find_template(category="characters", tags=["portrait"])

if template_id:
    result = await mcp_client.call_tool(
        "generate_image",
        {
            "template": template_id,
            "prompt": "heroic knight"
        }
    )
```

### Pattern 4: Error Recovery

Handle failures with retry logic.

```python
async def generate_with_retry(
    params: dict,
    max_retries: int = 3,
    timeout: float = 300.0
):
    """Generate with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            # Generate
            result = await mcp_client.call_tool("generate_image", params)
            prompt_id = result['prompt_id']

            # Wait with timeout
            start_time = time.time()

            while True:
                status = await mcp_client.call_tool(
                    "get_workflow_status",
                    {"prompt_id": prompt_id}
                )

                if status['state'] == 'completed':
                    return status

                if status['state'] == 'failed':
                    raise Exception(status.get('error', 'Unknown error'))

                if time.time() - start_time > timeout:
                    # Cancel and retry
                    await mcp_client.call_tool(
                        "cancel_workflow",
                        {"prompt_id": prompt_id}
                    )
                    raise TimeoutError("Generation timeout")

                await asyncio.sleep(2.0)

        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            await asyncio.sleep(5.0)
```

---

## Best Practices

### 1. Use Workflow Templates

Always prefer pre-built templates over custom workflows for common use cases:

```python
# Good: Use template
result = await mcp_client.call_tool(
    "generate_image",
    {"template": "character-portrait", "prompt": "elf warrior"}
)

# Less ideal: Custom workflow for common use case
result = await mcp_client.call_tool(
    "load_workflow",
    {"workflow_path": "./my_character_workflow.json"}
)
```

### 2. Set Appropriate Timeouts

Adjust timeouts based on workflow complexity:

```python
# Simple generation (512x512, 20 steps): 30-60s
# Standard generation (1024x1024, 30 steps): 60-120s
# High quality (1536x1536, 50 steps): 180-300s
# Upscaling workflows: 300-600s
```

### 3. Use Seeds for Reproducibility

Always specify seeds when you need reproducible results:

```python
# Reproducible generation
result = await mcp_client.call_tool(
    "generate_image",
    {
        "template": "item-icon",
        "prompt": "magic sword",
        "seed": 42  # Same result every time
    }
)

# Variations (random)
result = await mcp_client.call_tool(
    "generate_image",
    {
        "template": "item-icon",
        "prompt": "magic sword",
        "seed": -1  # Different result each time
    }
)
```

### 4. Poll Efficiently

Don't poll too frequently to avoid overloading the server:

```python
# Good: Poll every 2-3 seconds
await asyncio.sleep(2.0)

# Bad: Poll too frequently
await asyncio.sleep(0.1)  # Too fast!
```

### 5. Handle Errors Gracefully

Always check workflow status and handle failures:

```python
status = await mcp_client.call_tool(
    "get_workflow_status",
    {"prompt_id": prompt_id}
)

if status['state'] == 'failed':
    error = status.get('error', 'Unknown error')
    print(f"Generation failed: {error}")
    # Implement retry or fallback logic
```

### 6. Clean Up Resources

Cancel workflows that are no longer needed:

```python
try:
    result = await wait_for_completion(prompt_id, timeout=60.0)
except TimeoutError:
    # Cancel timed-out workflow
    await mcp_client.call_tool(
        "cancel_workflow",
        {"prompt_id": prompt_id}
    )
```

---

## Error Handling

### Common Errors

#### Connection Errors

**Error**: `Cannot connect to ComfyUI server`

**Cause**: ComfyUI is not running or URL is incorrect

**Solution**:
```python
# Verify ComfyUI is accessible
import aiohttp

async with aiohttp.ClientSession() as session:
    async with session.get("http://localhost:8188/system_stats") as resp:
        if resp.status == 200:
            print("ComfyUI is running")
```

#### Workflow Execution Errors

**Error**: `Workflow execution failed: Missing model file`

**Cause**: Required Stable Diffusion model not found

**Solution**:
- Download required model to ComfyUI's `models/checkpoints/` directory
- Update workflow to use available model

#### Timeout Errors

**Error**: `Workflow execution timeout`

**Cause**: Generation taking longer than configured timeout

**Solution**:
```python
# Increase timeout in configuration
{
  "env": {
    "COMFYUI_TIMEOUT": "300.0"  # 5 minutes
  }
}
```

#### Validation Errors

**Error**: `Invalid parameter: width must be multiple of 8`

**Cause**: Image dimensions not aligned to 8-pixel grid

**Solution**:
```python
# Ensure dimensions are multiples of 8
width = 512  # ✓ Valid
width = 513  # ✗ Invalid (not multiple of 8)
```

---

## Troubleshooting

### Issue: Tool Not Found

**Problem**: MCP client reports tool not available

**Solutions**:
1. Verify MCP server is running
2. Check `.mcp.json` configuration
3. Restart MCP client

### Issue: Slow Generation

**Problem**: Workflows taking too long to complete

**Solutions**:
1. Reduce `steps` parameter (20-30 for preview, 50+ for quality)
2. Lower image resolution
3. Check ComfyUI server resources (GPU, RAM)
4. Ensure no other intensive processes running

### Issue: Poor Image Quality

**Problem**: Generated images are low quality

**Solutions**:
1. Increase `steps` (30-50 range)
2. Adjust `cfg_scale` (7.0-8.5 typical)
3. Use better sampler (`dpm_2_ancestral`, `euler_ancestral`)
4. Improve prompt with more details
5. Use negative prompt to avoid unwanted features

### Issue: Workflow Stuck in Queue

**Problem**: Workflow remains in `queued` state

**Solutions**:
1. Check ComfyUI queue: `http://localhost:8188`
2. Cancel and retry:
   ```python
   await mcp_client.call_tool("cancel_workflow", {"prompt_id": prompt_id})
   ```
3. Restart ComfyUI server

---

## Examples

### Example 1: RPG Character Generation

```python
async def generate_rpg_character(
    character_type: str,
    appearance: str
):
    """Generate RPG character portrait."""
    prompt = f"{character_type}, {appearance}, detailed face, heroic pose"
    negative = "blurry, low quality, deformed, extra limbs"

    result = await mcp_client.call_tool(
        "generate_image",
        {
            "template": "character-portrait",
            "prompt": prompt,
            "negative_prompt": negative,
            "width": 512,
            "height": 768,
            "steps": 30,
            "cfg_scale": 7.5,
            "seed": -1
        }
    )

    return await wait_for_completion(result['prompt_id'])

# Usage
character = await generate_rpg_character(
    character_type="elf ranger",
    appearance="green cloak, bow and arrows, forest setting"
)
```

### Example 2: Item Icon Batch Generation

```python
async def generate_item_icons(items: list[str]):
    """Generate icons for multiple items."""
    tasks = []

    for item in items:
        task = mcp_client.call_tool(
            "generate_image",
            {
                "template": "item-icon",
                "prompt": f"{item}, detailed, centered, icon style",
                "negative_prompt": "background, blurry",
                "width": 512,
                "height": 512,
                "steps": 25
            }
        )
        tasks.append(task)

    # Submit all
    results = await asyncio.gather(*tasks)

    # Wait for completion
    prompt_ids = [r['prompt_id'] for r in results]
    final_results = await asyncio.gather(*[
        wait_for_completion(pid) for pid in prompt_ids
    ])

    return final_results

# Usage
items = ["iron sword", "health potion", "magic staff", "gold coin"]
icons = await generate_item_icons(items)
```

### Example 3: Environment Texture Generation

```python
async def generate_tileable_texture(
    texture_type: str,
    style: str = "realistic"
):
    """Generate tileable environment texture."""
    prompt = f"tileable {texture_type} texture, {style}, seamless pattern"

    result = await mcp_client.call_tool(
        "generate_image",
        {
            "template": "environment-texture",
            "prompt": prompt,
            "negative_prompt": "not tileable, seams, edges",
            "width": 1024,
            "height": 1024,
            "steps": 40,
            "cfg_scale": 7.0,
            "sampler": "dpm_2_ancestral"
        }
    )

    return await wait_for_completion(result['prompt_id'])

# Usage
grass_texture = await generate_tileable_texture(
    texture_type="grass",
    style="stylized cartoon"
)
```

### Example 4: Godot Integration

```python
# Godot GDScript example (pseudocode)
# Call MCP tools from Godot via HTTP bridge

func generate_character_portrait(character_name: String):
    var mcp_request = {
        "tool": "generate_image",
        "params": {
            "template": "character-portrait",
            "prompt": character_name + " portrait, detailed",
            "width": 512,
            "height": 512
        }
    }

    var http = HTTPRequest.new()
    add_child(http)
    http.connect("request_completed", self, "_on_generation_complete")
    http.request(MCP_SERVER_URL, [], true, HTTPClient.METHOD_POST, to_json(mcp_request))

func _on_generation_complete(result, response_code, headers, body):
    var json = JSON.parse(body.get_string_from_utf8())
    var prompt_id = json.result.prompt_id

    # Poll for completion
    poll_status(prompt_id)
```

---

## See Also

- **[API Reference](./API.md)** - Python API documentation
- **[Configuration Guide](./CONFIGURATION.md)** - Server configuration
- **[ComfyUI API Integration](./COMFYUI_API.md)** - REST API details
- **[Workflow Templates](./workflow-templates.md)** *(coming soon)* - Template creation guide
- **[Godot Integration](./godot-integration.md)** *(coming soon)* - Godot plugin documentation

---

**Version:** 0.1.0
**License:** MIT
**Repository:** https://github.com/PurlieuStudios/comfyui-mcp
