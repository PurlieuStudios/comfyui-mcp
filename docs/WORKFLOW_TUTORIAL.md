# ComfyUI Workflow Creation Tutorial

## Table of Contents

- [Introduction](#introduction)
- [Understanding ComfyUI Workflows](#understanding-comfyui-workflows)
- [Workflow JSON Structure](#workflow-json-structure)
- [Common Node Types](#common-node-types)
- [Creating Your First Workflow](#creating-your-first-workflow)
- [Parameter Substitution](#parameter-substitution)
- [Creating Workflow Templates](#creating-workflow-templates)
- [Advanced Techniques](#advanced-techniques)
- [Integration with MCP Server](#integration-with-mcp-server)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Complete Examples](#complete-examples)

---

## Introduction

This tutorial teaches you how to create, customize, and use ComfyUI workflows with the ComfyUI MCP Server. Whether you're building game assets, generating art, or automating image creation, this guide will help you master workflow creation.

### What You'll Learn

- ComfyUI workflow structure and node system
- Creating workflows from scratch
- Using parameter substitution for reusable templates
- Best practices for production workflows
- Integration with the MCP server

### Prerequisites

- Basic understanding of JSON format
- ComfyUI installed and running (see [README.md](../README.md))
- ComfyUI MCP Server configured (see [Installation](../README.md#installation))
- Familiarity with Stable Diffusion concepts (prompts, seeds, sampling)

---

## Understanding ComfyUI Workflows

### What is a ComfyUI Workflow?

ComfyUI workflows are **node-based graphs** that define image generation pipelines. Each workflow consists of:

1. **Nodes**: Processing steps (load model, encode text, sample, save image)
2. **Connections**: Data flow between nodes
3. **Parameters**: Configuration values for each node

### Why Use Workflows?

- **Reusability**: Create once, use many times with different parameters
- **Consistency**: Ensure all generated images follow the same process
- **Automation**: Programmatically generate images from game events
- **Flexibility**: Easily modify and extend generation pipelines

### Workflow Execution Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Load Model  │───▶│ Encode Text  │───▶│  Sample     │
│ (Checkpoint)│    │  (CLIP)      │    │  (KSampler) │
└─────────────┘    └──────────────┘    └─────────────┘
                          │                    │
                          ▼                    ▼
                   ┌──────────────┐    ┌─────────────┐
                   │ Encode Text  │    │ Decode Image│
                   │ (Negative)   │    │ (VAE)       │
                   └──────────────┘    └─────────────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ Save Image  │
                                       └─────────────┘
```

---

## Workflow JSON Structure

### Basic Structure

A ComfyUI workflow is a JSON object with nodes identified by string IDs:

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
      "text": "a beautiful landscape",
      "clip": ["1", 1]
    }
  }
}
```

### Node Structure

Each node has two required fields:

1. **`class_type`**: The type of ComfyUI node (e.g., `"KSampler"`, `"CheckpointLoaderSimple"`)
2. **`inputs`**: Dictionary of node parameters and connections

### Connection Format

Connections link node outputs to node inputs using the format:

```json
[node_id, output_slot]
```

**Example:**
```json
{
  "model": ["1", 0],    // Connect to node "1", output slot 0 (model)
  "clip": ["1", 1]      // Connect to node "1", output slot 1 (CLIP)
}
```

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
      "text": "a fantasy castle on a mountain",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "blurry, low quality, watermark",
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
      "negative": ["3", 0],
      "latent_image": ["5", 0]
    }
  },
  "5": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    }
  },
  "6": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["4", 0],
      "vae": ["1", 2]
    }
  },
  "7": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["6", 0],
      "filename_prefix": "castle"
    }
  }
}
```

---

## Common Node Types

### Core Nodes

#### `CheckpointLoaderSimple`

Loads a Stable Diffusion model checkpoint.

**Inputs:**
- `ckpt_name` (string): Checkpoint filename

**Outputs:**
- Slot 0: `MODEL`
- Slot 1: `CLIP`
- Slot 2: `VAE`

**Example:**
```json
{
  "class_type": "CheckpointLoaderSimple",
  "inputs": {
    "ckpt_name": "v1-5-pruned.safetensors"
  }
}
```

#### `CLIPTextEncode`

Encodes text prompts using CLIP.

**Inputs:**
- `text` (string): Text prompt
- `clip` (connection): CLIP model from checkpoint loader

**Outputs:**
- Slot 0: `CONDITIONING`

**Example:**
```json
{
  "class_type": "CLIPTextEncode",
  "inputs": {
    "text": "a warrior in armor",
    "clip": ["1", 1]
  }
}
```

#### `KSampler`

Performs the sampling process to generate images.

**Inputs:**
- `seed` (integer): Random seed for reproducibility
- `steps` (integer): Number of sampling steps (typically 20-50)
- `cfg` (float): Classifier-free guidance scale (typically 7.0)
- `sampler_name` (string): Sampler algorithm (`"euler"`, `"dpm_2"`, etc.)
- `scheduler` (string): Scheduler type (`"normal"`, `"karras"`, etc.)
- `denoise` (float): Denoising strength (0.0-1.0, typically 1.0 for full generation)
- `model` (connection): Model from checkpoint loader
- `positive` (connection): Positive prompt conditioning
- `negative` (connection): Negative prompt conditioning
- `latent_image` (connection): Latent space image

**Outputs:**
- Slot 0: `LATENT`

**Example:**
```json
{
  "class_type": "KSampler",
  "inputs": {
    "seed": 123456,
    "steps": 20,
    "cfg": 7.0,
    "sampler_name": "euler",
    "scheduler": "normal",
    "denoise": 1.0,
    "model": ["1", 0],
    "positive": ["2", 0],
    "negative": ["3", 0],
    "latent_image": ["5", 0]
  }
}
```

#### `EmptyLatentImage`

Creates a blank latent space image of specified dimensions.

**Inputs:**
- `width` (integer): Image width in pixels (must be multiple of 8)
- `height` (integer): Image height in pixels (must be multiple of 8)
- `batch_size` (integer): Number of images to generate (default: 1)

**Outputs:**
- Slot 0: `LATENT`

**Example:**
```json
{
  "class_type": "EmptyLatentImage",
  "inputs": {
    "width": 768,
    "height": 512,
    "batch_size": 1
  }
}
```

#### `VAEDecode`

Decodes latent space image to pixel space.

**Inputs:**
- `samples` (connection): Latent samples from KSampler
- `vae` (connection): VAE from checkpoint loader

**Outputs:**
- Slot 0: `IMAGE`

**Example:**
```json
{
  "class_type": "VAEDecode",
  "inputs": {
    "samples": ["4", 0],
    "vae": ["1", 2]
  }
}
```

#### `SaveImage`

Saves the generated image to disk.

**Inputs:**
- `images` (connection): Images from VAE decoder
- `filename_prefix` (string): Prefix for saved filenames

**Outputs:**
- None (terminal node)

**Example:**
```json
{
  "class_type": "SaveImage",
  "inputs": {
    "images": ["6", 0],
    "filename_prefix": "character_portrait"
  }
}
```

### Advanced Nodes

#### `LoraLoader`

Applies LoRA (Low-Rank Adaptation) models to enhance or modify generation.

**Inputs:**
- `model` (connection): Base model
- `clip` (connection): CLIP model
- `lora_name` (string): LoRA filename
- `strength_model` (float): LoRA strength for model (0.0-1.0)
- `strength_clip` (float): LoRA strength for CLIP (0.0-1.0)

**Outputs:**
- Slot 0: `MODEL`
- Slot 1: `CLIP`

#### `ControlNetLoader` + `ControlNetApply`

Applies ControlNet for precise control over generation using reference images.

**ControlNetLoader Inputs:**
- `control_net_name` (string): ControlNet model filename

**ControlNetApply Inputs:**
- `conditioning` (connection): Positive conditioning
- `control_net` (connection): ControlNet from loader
- `image` (connection): Control image
- `strength` (float): ControlNet strength (0.0-1.0)

#### `UpscaleModelLoader` + `ImageUpscaleWithModel`

Upscales generated images using AI models (e.g., ESRGAN, RealESRGAN).

**UpscaleModelLoader Inputs:**
- `model_name` (string): Upscale model filename

**ImageUpscaleWithModel Inputs:**
- `upscale_model` (connection): Upscale model from loader
- `image` (connection): Image to upscale

---

## Creating Your First Workflow

### Step 1: Plan Your Workflow

Before writing JSON, plan your node graph:

1. **What do you want to generate?** (character, environment, item)
2. **What nodes are needed?** (minimum: loader, encoders, sampler, VAE, save)
3. **What parameters should be configurable?** (prompt, size, seed, steps)

### Step 2: Create the Base Workflow

Let's create a simple character portrait generator.

**Required Nodes:**
- CheckpointLoaderSimple (node 1)
- CLIPTextEncode for positive prompt (node 2)
- CLIPTextEncode for negative prompt (node 3)
- EmptyLatentImage (node 4)
- KSampler (node 5)
- VAEDecode (node 6)
- SaveImage (node 7)

### Step 3: Write the JSON

Create `workflows/character_portrait.json`:

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
      "text": "portrait of a fantasy warrior, detailed face, armor, heroic pose",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "blurry, low quality, deformed, ugly, bad anatomy",
      "clip": ["1", 1]
    }
  },
  "4": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": 512,
      "height": 768,
      "batch_size": 1
    }
  },
  "5": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0],
      "latent_image": ["4", 0]
    }
  },
  "6": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    }
  },
  "7": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["6", 0],
      "filename_prefix": "character_portrait"
    }
  }
}
```

### Step 4: Test Your Workflow

Using the ComfyUI MCP Python API:

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig, WorkflowPrompt, WorkflowNode

async def test_workflow():
    # Load workflow JSON
    import json
    with open("workflows/character_portrait.json") as f:
        workflow_json = json.load(f)

    # Convert to WorkflowPrompt
    nodes = {
        node_id: WorkflowNode(**node_data)
        for node_id, node_data in workflow_json.items()
    }
    workflow = WorkflowPrompt(nodes=nodes)

    # Submit to ComfyUI
    config = ComfyUIConfig(url="http://localhost:8188")
    async with ComfyUIClient(config) as client:
        prompt_id = await client.submit_workflow(workflow)
        print(f"Submitted workflow: {prompt_id}")

        # Wait for completion
        result = await client.wait_for_result(prompt_id)
        print(f"Generated images: {result.images}")

asyncio.run(test_workflow())
```

---

## Parameter Substitution

### Why Parameter Substitution?

Hard-coded values limit workflow reusability. Parameter substitution allows:

- **Dynamic prompts**: Change text without editing JSON
- **Variable dimensions**: Generate different image sizes
- **Different seeds**: Create variations of the same prompt
- **Configuration reuse**: One workflow, many use cases

### Placeholder Syntax

Use `{{parameter_name}}` in your workflow JSON:

```json
{
  "class_type": "CLIPTextEncode",
  "inputs": {
    "text": "{{prompt}}",
    "clip": ["1", 1]
  }
}
```

### Creating Parameterized Workflows

Modify the character portrait workflow to use placeholders:

**`workflows/character_portrait_template.json`:**

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "{{model}}"
    }
  },
  "2": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "{{prompt}}",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "{{negative_prompt}}",
      "clip": ["1", 1]
    }
  },
  "4": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": "{{width}}",
      "height": "{{height}}",
      "batch_size": 1
    }
  },
  "5": {
    "class_type": "KSampler",
    "inputs": {
      "seed": "{{seed}}",
      "steps": "{{steps}}",
      "cfg": "{{cfg}}",
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0],
      "latent_image": ["4", 0]
    }
  },
  "6": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    }
  },
  "7": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["6", 0],
      "filename_prefix": "character_{{seed}}"
    }
  }
}
```

### Using Parameterized Workflows

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

async def generate_character():
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        # Use MCP generate_image with template
        result = await client.generate_image(
            template="character-portrait",
            params={
                "prompt": "elf ranger with bow, forest background",
                "negative_prompt": "blurry, low quality",
                "width": 512,
                "height": 768,
                "steps": 25,
                "cfg": 7.5,
                "seed": 12345,
                "model": "v1-5-pruned.safetensors"
            }
        )

        print(f"Generated: {result.images}")

asyncio.run(generate_character())
```

---

## Creating Workflow Templates

### WorkflowTemplate Model

The ComfyUI MCP server uses `WorkflowTemplate` objects for reusable workflows:

```python
from comfyui_mcp import WorkflowTemplate, TemplateParameter, WorkflowNode

template = WorkflowTemplate(
    name="Character Portrait Generator",
    description="Generates character portraits with customizable prompts and dimensions",
    category="character",
    parameters={
        "prompt": TemplateParameter(
            name="prompt",
            description="Character description prompt",
            type="string",
            default="a fantasy warrior",
            required=True
        ),
        "width": TemplateParameter(
            name="width",
            description="Image width in pixels",
            type="int",
            default=512,
            required=False
        ),
        "height": TemplateParameter(
            name="height",
            description="Image height in pixels",
            type="int",
            default=768,
            required=False
        ),
        "seed": TemplateParameter(
            name="seed",
            description="Random seed for reproducibility",
            type="int",
            default=42,
            required=False
        ),
        "steps": TemplateParameter(
            name="steps",
            description="Number of sampling steps",
            type="int",
            default=25,
            required=False
        )
    },
    nodes={
        "1": WorkflowNode(
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "v1-5-pruned.safetensors"}
        ),
        "2": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={"text": "{{prompt}}", "clip": ["1", 1]}
        ),
        "3": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={
                "text": "blurry, low quality, deformed",
                "clip": ["1", 1]
            }
        ),
        "4": WorkflowNode(
            class_type="EmptyLatentImage",
            inputs={
                "width": "{{width}}",
                "height": "{{height}}",
                "batch_size": 1
            }
        ),
        "5": WorkflowNode(
            class_type="KSampler",
            inputs={
                "seed": "{{seed}}",
                "steps": "{{steps}}",
                "cfg": 7.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            }
        ),
        "6": WorkflowNode(
            class_type="VAEDecode",
            inputs={"samples": ["5", 0], "vae": ["1", 2]}
        ),
        "7": WorkflowNode(
            class_type="SaveImage",
            inputs={"images": ["6", 0], "filename_prefix": "character"}
        )
    }
)
```

### Template Instantiation

Templates are instantiated with specific parameter values:

```python
# Create a workflow from the template
workflow = template.instantiate({
    "prompt": "dwarf blacksmith with hammer",
    "width": 768,
    "height": 768,
    "seed": 99999,
    "steps": 30
})

# Submit the workflow
async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)
    result = await client.wait_for_result(prompt_id)
```

### Template Categories

Organize templates by category:

- **`character`**: Character portraits, NPCs, player avatars
- **`item`**: Weapon icons, item sprites, inventory graphics
- **`environment`**: Backgrounds, textures, environmental assets
- **`ui`**: UI elements, icons, buttons

---

## Advanced Techniques

### Batch Generation

Generate multiple variations in one workflow:

```json
{
  "4": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 4
    }
  }
}
```

This generates 4 images in parallel with different noise patterns.

### LoRA Integration

Enhance generation with LoRA models:

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "v1-5-pruned.safetensors"
    }
  },
  "2": {
    "class_type": "LoraLoader",
    "inputs": {
      "model": ["1", 0],
      "clip": ["1", 1],
      "lora_name": "fantasy_style.safetensors",
      "strength_model": 0.8,
      "strength_clip": 0.8
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "{{prompt}}",
      "clip": ["2", 1]
    }
  }
}
```

### Image-to-Image Workflows

Use existing images as starting points:

```json
{
  "1": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "reference.png"
    }
  },
  "2": {
    "class_type": "VAEEncode",
    "inputs": {
      "pixels": ["1", 0],
      "vae": ["3", 2]
    }
  },
  "3": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "v1-5-pruned.safetensors"
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
      "denoise": 0.7,
      "model": ["3", 0],
      "positive": ["5", 0],
      "negative": ["6", 0],
      "latent_image": ["2", 0]
    }
  }
}
```

Note the `denoise` value of `0.7` (instead of `1.0`) preserves more of the original image.

### ControlNet for Precise Control

Use reference images for pose/composition control:

```json
{
  "1": {
    "class_type": "ControlNetLoader",
    "inputs": {
      "control_net_name": "control_openpose.pth"
    }
  },
  "2": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "pose_reference.png"
    }
  },
  "3": {
    "class_type": "ControlNetApply",
    "inputs": {
      "conditioning": ["4", 0],
      "control_net": ["1", 0],
      "image": ["2", 0],
      "strength": 0.9
    }
  }
}
```

### Multi-Stage Workflows

Chain multiple samplers for refinement:

```json
{
  "5": {
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
      "negative": ["3", 0],
      "latent_image": ["4", 0]
    }
  },
  "6": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 43,
      "steps": 10,
      "cfg": 7.0,
      "sampler_name": "dpm_2",
      "scheduler": "karras",
      "denoise": 0.5,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0],
      "latent_image": ["5", 0]
    }
  }
}
```

---

## Integration with MCP Server

### Loading Custom Workflows

Use the `load_workflow` MCP tool to load custom workflows:

**Via Claude Code:**
```
User: Load my custom workflow from workflows/my_workflow.json
```

**Via Python API:**
```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

async def load_custom():
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        workflow = await client.load_workflow("workflows/my_workflow.json")
        print(f"Loaded workflow with {len(workflow.nodes)} nodes")

asyncio.run(load_custom())
```

**Via JSON-RPC:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "load_workflow",
    "arguments": {
      "workflow_path": "workflows/my_workflow.json"
    }
  },
  "id": 1
}
```

### Generating Images with Templates

Use the `generate_image` MCP tool:

**Via Claude Code:**
```
User: Generate a character portrait with prompt "cyberpunk hacker" using seed 12345
```

**Via Python API:**
```python
result = await client.generate_image(
    template="character-portrait",
    params={
        "prompt": "cyberpunk hacker",
        "seed": 12345,
        "width": 512,
        "height": 768
    }
)
```

### Workflow Status Tracking

Monitor workflow execution:

```python
# Submit workflow
prompt_id = await client.submit_workflow(workflow)

# Check status periodically
while True:
    status = await client.get_workflow_status(prompt_id)

    if status.state == "completed":
        result = await client.get_result(prompt_id)
        break
    elif status.state == "failed":
        print("Generation failed!")
        break

    print(f"Progress: {status.progress * 100:.0f}%")
    await asyncio.sleep(1.0)
```

### Cancelling Workflows

Cancel long-running workflows:

```python
# Cancel specific workflow
await client.cancel_workflow(prompt_id)

# Or interrupt current execution
await client.interrupt()
```

---

## Best Practices

### 1. Use Descriptive Node IDs

While ComfyUI accepts any string IDs, use meaningful numbers or names:

```json
{
  "checkpoint_loader": {...},
  "positive_prompt": {...},
  "sampler": {...}
}
```

Or sequential numbers:
```json
{
  "1": {...},
  "2": {...},
  "3": {...}
}
```

### 2. Set Reasonable Defaults

Choose default parameter values that work well for most cases:

```python
TemplateParameter(
    name="steps",
    description="Number of sampling steps",
    type="int",
    default=25,  # Good balance of quality and speed
    required=False
)
```

### 3. Validate Parameters

Ensure parameters are within valid ranges:

- **Width/Height**: Must be multiples of 8 (typically 512, 768, 1024)
- **Steps**: 15-50 for most cases
- **CFG**: 5.0-15.0 (typically 7.0-8.0)
- **Seed**: Any integer (use -1 for random)

### 4. Use Meaningful Negative Prompts

Always include negative prompts to improve quality:

```json
{
  "text": "blurry, low quality, deformed, ugly, bad anatomy, watermark, signature"
}
```

### 5. Optimize Batch Sizes

For multiple variations, use batch generation:

- **batch_size=1**: Generate one image
- **batch_size=4**: Generate 4 variations (faster than 4 separate generations)

### 6. Handle Seeds Properly

- **Fixed seed**: Reproducible results for testing
- **Random seed**: Variety in production (use `random.randint(0, 2**32-1)`)
- **Seed sequences**: Predictable variations (seed, seed+1, seed+2, ...)

### 7. Save Metadata

Include generation metadata in filenames or separate files:

```json
{
  "class_type": "SaveImage",
  "inputs": {
    "images": ["6", 0],
    "filename_prefix": "char_{{prompt}}_s{{seed}}_st{{steps}}"
  }
}
```

### 8. Test Incrementally

When creating complex workflows:

1. Start with basic workflow (loader → sampler → save)
2. Test that it works
3. Add one feature at a time (LoRA, ControlNet, etc.)
4. Test after each addition

### 9. Document Your Templates

Add clear descriptions and examples:

```python
WorkflowTemplate(
    name="Character Portrait",
    description="""
    Generates character portraits suitable for RPG games.

    Features:
    - Portrait orientation (512x768)
    - Optimized for faces and upper body
    - Good detail preservation

    Best for:
    - NPC portraits
    - Character selection screens
    - Dialogue portraits
    """,
    ...
)
```

### 10. Version Control Your Workflows

Store workflow JSON in version control:

```
workflows/
├── character_portrait_v1.json
├── character_portrait_v2.json  # Improved version
├── item_icon_v1.json
└── environment_bg_v1.json
```

---

## Troubleshooting

### Common Issues

#### Issue: "Model not found"

**Symptoms:**
```
Error: CheckpointLoaderSimple failed: Model "model.safetensors" not found
```

**Solution:**
- Ensure the model file exists in ComfyUI's `models/checkpoints/` directory
- Check the exact filename (case-sensitive)
- Verify the model downloaded completely

#### Issue: "Invalid dimensions"

**Symptoms:**
```
Error: Width/height must be multiples of 8
```

**Solution:**
- Use dimensions divisible by 8: 512, 768, 1024
- Avoid odd dimensions: ~~513~~, ~~767~~

#### Issue: "Node connection failed"

**Symptoms:**
```
Error: Node "5" input "model" expects connection but got ["99", 0]
```

**Solution:**
- Ensure the connected node ID exists: `"99"` must be defined
- Check the output slot number: node outputs vary by type
- Verify connection format: `[node_id, slot]`

#### Issue: "Generation takes too long"

**Solutions:**
1. Reduce `steps` (try 15-20 instead of 50)
2. Reduce image dimensions (512x512 instead of 1024x1024)
3. Reduce `batch_size` (1 instead of 4)
4. Check ComfyUI server load

#### Issue: "Out of memory"

**Solutions:**
1. Reduce image dimensions
2. Reduce batch size
3. Close other ComfyUI workflows
4. Restart ComfyUI server
5. Use smaller models (pruned versions)

#### Issue: "Poor image quality"

**Solutions:**
1. Increase `steps` (try 25-30)
2. Adjust `cfg` (try 7.0-8.0)
3. Improve prompt quality
4. Add detailed negative prompts
5. Use better base models
6. Try different samplers

### Debugging Workflows

#### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

#### Validate Workflow Structure

```python
from comfyui_mcp import WorkflowPrompt, WorkflowNode

try:
    workflow = WorkflowPrompt(nodes={...})
    print("Workflow validation passed!")
except Exception as e:
    print(f"Validation error: {e}")
```

#### Test Individual Nodes

Create minimal workflows to test specific nodes:

```python
# Test just the model loader
minimal_workflow = WorkflowPrompt(nodes={
    "1": WorkflowNode(
        class_type="CheckpointLoaderSimple",
        inputs={"ckpt_name": "v1-5-pruned.safetensors"}
    )
})
```

#### Check ComfyUI Server Logs

Monitor ComfyUI console output for errors:
- Node execution failures
- Model loading issues
- Memory errors

---

## Complete Examples

### Example 1: RPG Character Generator

Complete workflow for generating RPG character portraits:

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "v1-5-pruned.safetensors"
    }
  },
  "2": {
    "class_type": "LoraLoader",
    "inputs": {
      "model": ["1", 0],
      "clip": ["1", 1],
      "lora_name": "fantasy_rpg_style.safetensors",
      "strength_model": 0.7,
      "strength_clip": 0.7
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "{{prompt}}, detailed face, fantasy art, character portrait, sharp focus",
      "clip": ["2", 1]
    }
  },
  "4": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "blurry, low quality, deformed, ugly, bad anatomy, duplicate, multiple people",
      "clip": ["2", 1]
    }
  },
  "5": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": 512,
      "height": 768,
      "batch_size": 1
    }
  },
  "6": {
    "class_type": "KSampler",
    "inputs": {
      "seed": "{{seed}}",
      "steps": "{{steps}}",
      "cfg": 7.5,
      "sampler_name": "dpm_2",
      "scheduler": "karras",
      "denoise": 1.0,
      "model": ["2", 0],
      "positive": ["3", 0],
      "negative": ["4", 0],
      "latent_image": ["5", 0]
    }
  },
  "7": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["6", 0],
      "vae": ["1", 2]
    }
  },
  "8": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["7", 0],
      "filename_prefix": "rpg_character_{{seed}}"
    }
  }
}
```

**Usage:**
```python
result = await client.generate_image(
    template="rpg-character",
    params={
        "prompt": "female elf mage with staff, blue robes",
        "seed": 42,
        "steps": 30
    }
)
```

### Example 2: Item Icon Generator

Workflow optimized for game item icons:

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
      "text": "{{prompt}}, game icon, item, centered, simple background, high detail",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "blurry, low quality, hands, people, text, watermark",
      "clip": ["1", 1]
    }
  },
  "4": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    }
  },
  "5": {
    "class_type": "KSampler",
    "inputs": {
      "seed": "{{seed}}",
      "steps": 25,
      "cfg": 8.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0],
      "latent_image": ["4", 0]
    }
  },
  "6": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    }
  },
  "7": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["6", 0],
      "filename_prefix": "item_{{seed}}"
    }
  }
}
```

**Usage:**
```python
result = await client.generate_image(
    template="item-icon",
    params={
        "prompt": "legendary sword with glowing runes",
        "seed": 99999
    }
)
```

### Example 3: Environment Background Generator

Workflow for generating game environment backgrounds:

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
      "text": "{{prompt}}, wide angle, landscape, environment art, detailed background",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "people, characters, blurry, low quality, text, watermark",
      "clip": ["1", 1]
    }
  },
  "4": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": "{{width}}",
      "height": "{{height}}",
      "batch_size": 1
    }
  },
  "5": {
    "class_type": "KSampler",
    "inputs": {
      "seed": "{{seed}}",
      "steps": 30,
      "cfg": 7.0,
      "sampler_name": "dpm_2",
      "scheduler": "karras",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0],
      "latent_image": ["4", 0]
    }
  },
  "6": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    }
  },
  "7": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["6", 0],
      "filename_prefix": "env_{{seed}}"
    }
  }
}
```

**Usage:**
```python
result = await client.generate_image(
    template="environment-background",
    params={
        "prompt": "mystical forest with glowing mushrooms, foggy atmosphere",
        "width": 1024,
        "height": 576,
        "seed": 77777
    }
)
```

---

## Conclusion

You now have comprehensive knowledge of ComfyUI workflow creation! You've learned:

✅ Workflow structure and node system
✅ Common node types and their parameters
✅ Creating workflows from scratch
✅ Parameter substitution for reusable templates
✅ Advanced techniques (LoRA, ControlNet, batching)
✅ Integration with the MCP server
✅ Best practices and troubleshooting

### Next Steps

1. **Experiment**: Create your own workflows for specific use cases
2. **Optimize**: Fine-tune parameters for your needs
3. **Share**: Contribute workflow templates to the community
4. **Integrate**: Connect workflows to your game or application

### Additional Resources

- **[README.md](../README.md)** - Project overview and quick start
- **[MCP_TOOLS.md](MCP_TOOLS.md)** - Complete MCP tool reference
- **[API.md](API.md)** - Python API documentation
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines
- **[ComfyUI Docs](https://github.com/comfyanonymous/ComfyUI)** - Official ComfyUI documentation

### Getting Help

- **[GitHub Issues](https://github.com/PurlieuStudios/comfyui-mcp/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/PurlieuStudios/comfyui-mcp/discussions)** - Q&A and community support

---

**Version:** 1.0.0
**Last Updated:** 2025-01-18
**Maintainer:** [Purlieu Studios](https://purlieu.studio)
