# Workflow Template System

## Table of Contents

- [Overview](#overview)
- [Why Use Templates?](#why-use-templates)
- [Template Structure](#template-structure)
- [Template File Format](#template-file-format)
- [Creating Templates](#creating-templates)
- [Using Templates](#using-templates)
- [Built-in Templates](#built-in-templates)
- [Parameter Substitution](#parameter-substitution)
- [Template Manager](#template-manager)
- [Best Practices](#best-practices)
- [Complete Examples](#complete-examples)
- [Advanced Topics](#advanced-topics)

---

## Overview

The ComfyUI MCP Server workflow template system provides a powerful, reusable approach to image generation. Templates encapsulate complete ComfyUI workflows with configurable parameters, allowing you to generate images with consistent quality while varying specific aspects like prompts, dimensions, and generation settings.

### What is a Workflow Template?

A workflow template is a **parameterized ComfyUI workflow** that:

- Defines a complete image generation pipeline
- Specifies customizable parameters with defaults
- Supports parameter substitution using `{{placeholder}}` syntax
- Includes metadata for organization and discovery
- Can be instantiated multiple times with different values

### Key Components

1. **WorkflowTemplate** - The template definition (metadata + workflow structure)
2. **TemplateParameter** - Individual parameter definitions with types and defaults
3. **WorkflowPrompt** - Instantiated workflow ready for execution
4. **Parameter Substitution Engine** - Replaces placeholders with actual values

---

## Why Use Templates?

### Benefits

**Consistency**
- Ensure all generated images follow the same quality standards
- Maintain consistent style across game assets
- Reproduce results reliably

**Reusability**
- Create once, use many times with different parameters
- Share templates across projects and teams
- Build libraries of proven workflows

**Maintainability**
- Update workflow in one place, affects all uses
- Version control template definitions
- Document workflow intent and parameters

**Productivity**
- Faster iteration on asset generation
- Reduce manual workflow configuration
- Enable batch generation workflows

### Use Cases

- **Game Asset Generation**: Characters, items, environments, UI elements
- **Batch Processing**: Generate hundreds of variations efficiently
- **Automated Pipelines**: Integrate into build systems
- **Rapid Prototyping**: Quick iteration on asset styles
- **Team Collaboration**: Share standardized workflows

---

## Template Structure

### WorkflowTemplate Model

The `WorkflowTemplate` Pydantic model defines the complete template structure:

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
        "seed": TemplateParameter(
            name="seed",
            description="Random seed for reproducibility",
            type="int",
            default=42,
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
        # ... more nodes
    }
)
```

### Template Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable template name |
| `description` | string | Yes | Detailed description of what the template generates |
| `category` | string | No | Template category for organization |
| `parameters` | dict | Yes | Dictionary of parameter definitions |
| `nodes` | dict | Yes | ComfyUI workflow nodes with placeholders |

### TemplateParameter Model

Each parameter is defined using the `TemplateParameter` model:

```python
from comfyui_mcp import TemplateParameter

parameter = TemplateParameter(
    name="steps",
    description="Number of sampling steps",
    type="int",
    default=25,
    required=False
)
```

### Parameter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Parameter name (used in placeholders) |
| `description` | string | Yes | Human-readable description |
| `type` | string | Yes | Parameter type: "string", "int", "float", "bool" |
| `default` | any | Yes | Default value for the parameter |
| `required` | boolean | No | Whether parameter must be provided (default: True) |

### Parameter Types

**Supported Types:**

- **`"string"`** - Text values (prompts, model names, file paths)
- **`"int"`** - Integer values (dimensions, steps, seeds)
- **`"float"`** - Decimal values (CFG scale, denoise strength)
- **`"bool"`** - Boolean values (enable/disable features)

---

## Template File Format

### JSON Schema

Templates can be stored as JSON files for easy sharing and version control:

```json
{
  "name": "Character Portrait Generator",
  "description": "Generates character portraits with customizable prompts",
  "category": "character",
  "parameters": {
    "prompt": {
      "name": "prompt",
      "description": "Character description prompt",
      "type": "string",
      "default": "a fantasy warrior",
      "required": true
    },
    "width": {
      "name": "width",
      "description": "Image width in pixels",
      "type": "int",
      "default": 512,
      "required": false
    },
    "height": {
      "name": "height",
      "description": "Image height in pixels",
      "type": "int",
      "default": 768,
      "required": false
    },
    "seed": {
      "name": "seed",
      "description": "Random seed for reproducibility",
      "type": "int",
      "default": 42,
      "required": false
    },
    "steps": {
      "name": "steps",
      "description": "Number of sampling steps",
      "type": "int",
      "default": 25,
      "required": false
    },
    "cfg": {
      "name": "cfg",
      "description": "Classifier-free guidance scale",
      "type": "float",
      "default": 7.5,
      "required": false
    }
  },
  "nodes": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "v1-5-pruned.safetensors"
      }
    },
    "2": {
      "class_type": "CLIPTextEncode",
      "inputs": {
        "text": "{{prompt}}, detailed face, fantasy art, character portrait",
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
}
```

### File Organization

Recommended directory structure for template files:

```
workflows/
├── character-portrait.json      # Character templates
├── item-icon.json              # Item templates
├── environment-bg.json         # Environment templates
├── pixel-art.json              # Pixel art templates
└── custom/                     # Custom templates
    ├── my-template.json
    └── team-template.json
```

---

## Creating Templates

### Step 1: Design Your Workflow

Before creating a template, design and test your ComfyUI workflow:

1. Open ComfyUI and create your workflow
2. Test with various inputs to ensure quality
3. Identify which values should be parameters
4. Document the workflow's purpose and use cases

### Step 2: Identify Parameters

Determine which values should be parameterizable:

**Common Parameters:**
- Text prompts (positive and negative)
- Image dimensions (width, height)
- Sampling settings (steps, CFG, seed)
- Model names (checkpoint, LoRA, ControlNet)
- Output settings (filename prefix, format)

**Guidelines:**
- Make frequently changed values parameters
- Keep stable values hard-coded
- Provide sensible defaults for all parameters
- Document parameter constraints

### Step 3: Create Template Definition

#### Python API

```python
from comfyui_mcp import WorkflowTemplate, TemplateParameter, WorkflowNode

# Define parameters
parameters = {
    "prompt": TemplateParameter(
        name="prompt",
        description="Main text prompt describing the image",
        type="string",
        default="a beautiful landscape",
        required=True
    ),
    "negative_prompt": TemplateParameter(
        name="negative_prompt",
        description="Negative prompt (things to avoid)",
        type="string",
        default="blurry, low quality, watermark",
        required=False
    ),
    "width": TemplateParameter(
        name="width",
        description="Image width in pixels (multiple of 8)",
        type="int",
        default=512,
        required=False
    ),
    "height": TemplateParameter(
        name="height",
        description="Image height in pixels (multiple of 8)",
        type="int",
        default=512,
        required=False
    ),
    "steps": TemplateParameter(
        name="steps",
        description="Number of sampling steps (15-50)",
        type="int",
        default=20,
        required=False
    ),
    "seed": TemplateParameter(
        name="seed",
        description="Random seed (-1 for random)",
        type="int",
        default=42,
        required=False
    )
}

# Define workflow nodes with placeholders
nodes = {
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
        inputs={"text": "{{negative_prompt}}", "clip": ["1", 1]}
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
            "cfg": 7.0,
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
        inputs={"images": ["6", 0], "filename_prefix": "output"}
    )
}

# Create template
template = WorkflowTemplate(
    name="Simple Image Generator",
    description="Basic text-to-image generation workflow",
    category="general",
    parameters=parameters,
    nodes=nodes
)

# Save to JSON file
import json
with open("workflows/simple-generator.json", "w") as f:
    json.dump(template.model_dump(), f, indent=2)
```

#### JSON File

Alternatively, create the JSON file directly (see [Template File Format](#template-file-format) above).

### Step 4: Test Your Template

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

async def test_template():
    # Load template
    import json
    with open("workflows/simple-generator.json") as f:
        template_data = json.load(f)

    template = WorkflowTemplate(**template_data)

    # Instantiate with test values
    workflow = template.instantiate({
        "prompt": "cyberpunk city at night",
        "width": 768,
        "height": 512,
        "steps": 30,
        "seed": 12345
    })

    # Submit to ComfyUI
    config = ComfyUIConfig(url="http://localhost:8188")
    async with ComfyUIClient(config) as client:
        prompt_id = await client.submit_workflow(workflow)
        result = await client.wait_for_result(prompt_id)
        print(f"Generated: {result.images}")

asyncio.run(test_template())
```

---

## Using Templates

### Loading Templates

#### From Python

```python
from comfyui_mcp import WorkflowTemplate
import json

# Load from JSON file
with open("workflows/character-portrait.json") as f:
    template_data = json.load(f)

template = WorkflowTemplate(**template_data)
```

#### Using WorkflowTemplateManager

```python
from comfyui_mcp import WorkflowTemplateManager

# Initialize manager
manager = WorkflowTemplateManager(templates_dir="workflows/")

# Load specific template
template = manager.load_template("character-portrait")

# List all templates
templates = manager.list_templates()
for tmpl in templates:
    print(f"{tmpl.name} - {tmpl.description}")

# Find templates by category
character_templates = manager.find_by_category("character")
```

### Instantiating Templates

#### With Custom Parameters

```python
# Instantiate with specific values
workflow = template.instantiate({
    "prompt": "elf ranger with bow, forest background",
    "negative_prompt": "blurry, low quality, deformed",
    "width": 512,
    "height": 768,
    "steps": 25,
    "seed": 99999
})
```

#### With Defaults

```python
# Use default values (only override what you need)
workflow = template.instantiate({
    "prompt": "dwarf blacksmith with hammer"
    # Other parameters use defaults from template
})
```

#### Multiple Instantiations

```python
# Generate multiple variations
prompts = [
    "warrior with sword",
    "mage with staff",
    "rogue with daggers",
    "cleric with holy symbol"
]

workflows = [
    template.instantiate({"prompt": prompt, "seed": i})
    for i, prompt in enumerate(prompts)
]
```

### Executing Templates

#### Submit and Wait

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

async def generate_image(template, params):
    # Instantiate template
    workflow = template.instantiate(params)

    # Submit to ComfyUI
    config = ComfyUIConfig(url="http://localhost:8188")
    async with ComfyUIClient(config) as client:
        prompt_id = await client.submit_workflow(workflow)
        result = await client.wait_for_result(prompt_id)
        return result.images

# Run
images = asyncio.run(generate_image(template, {
    "prompt": "fantasy castle on a mountain"
}))
```

#### With Progress Tracking

```python
async def generate_with_progress(template, params):
    workflow = template.instantiate(params)

    config = ComfyUIConfig(url="http://localhost:8188")
    async with ComfyUIClient(config) as client:
        # Submit workflow
        prompt_id = await client.submit_workflow(workflow)

        # Track progress
        while True:
            status = await client.get_workflow_status(prompt_id)

            if status.state == "completed":
                result = await client.get_result(prompt_id)
                return result.images
            elif status.state == "failed":
                raise Exception("Generation failed")

            print(f"Progress: {status.progress * 100:.0f}%")
            await asyncio.sleep(1.0)
```

#### Batch Generation

```python
async def batch_generate(template, param_list):
    config = ComfyUIConfig(url="http://localhost:8188")
    async with ComfyUIClient(config) as client:
        results = []

        for params in param_list:
            workflow = template.instantiate(params)
            prompt_id = await client.submit_workflow(workflow)
            result = await client.wait_for_result(prompt_id)
            results.append(result.images)

        return results

# Generate batch
batch_params = [
    {"prompt": "warrior", "seed": 1},
    {"prompt": "mage", "seed": 2},
    {"prompt": "rogue", "seed": 3}
]

all_images = asyncio.run(batch_generate(template, batch_params))
```

---

## Built-in Templates

The ComfyUI MCP Server includes four standard templates for common game asset types:

### 1. Character Portrait (`character-portrait`)

**Purpose**: Generate character portraits and avatars for RPGs and games

**Dimensions**: 512×768 (portrait orientation)

**Parameters**:
- `prompt` (string, required) - Character description
- `negative_prompt` (string) - Things to avoid
- `width` (int) - Image width (default: 512)
- `height` (int) - Image height (default: 768)
- `steps` (int) - Sampling steps (default: 25)
- `cfg` (float) - CFG scale (default: 7.5)
- `seed` (int) - Random seed (default: 42)

**Use Cases**:
- NPC portraits
- Player character avatars
- Dialogue portraits
- Character selection screens

**Example**:
```python
workflow = template.instantiate({
    "prompt": "female elf mage, blue robes, staff, detailed face",
    "seed": 12345,
    "steps": 30
})
```

### 2. Item Icon (`item-icon`)

**Purpose**: Generate item icons for inventory systems

**Dimensions**: 512×512 (square, centered)

**Parameters**:
- `prompt` (string, required) - Item description
- `negative_prompt` (string) - Things to avoid (default includes "people, hands")
- `width` (int) - Image width (default: 512)
- `height` (int) - Image height (default: 512)
- `steps` (int) - Sampling steps (default: 20)
- `cfg` (float) - CFG scale (default: 8.0)
- `seed` (int) - Random seed (default: 42)

**Use Cases**:
- Weapon icons
- Potion and consumable icons
- Equipment icons
- Resource icons

**Example**:
```python
workflow = template.instantiate({
    "prompt": "legendary sword with glowing runes, game icon, centered",
    "seed": 99999
})
```

### 3. Environment Background (`environment-bg`)

**Purpose**: Generate background images and environmental textures

**Dimensions**: 1024×576 (16:9 aspect ratio)

**Parameters**:
- `prompt` (string, required) - Environment description
- `negative_prompt` (string) - Things to avoid (default includes "people, characters")
- `width` (int) - Image width (default: 1024)
- `height` (int) - Image height (default: 576)
- `steps` (int) - Sampling steps (default: 30)
- `cfg` (float) - CFG scale (default: 7.0)
- `seed` (int) - Random seed (default: 42)

**Use Cases**:
- Level backgrounds
- Menu backgrounds
- Environmental textures
- Parallax layers

**Example**:
```python
workflow = template.instantiate({
    "prompt": "mystical forest with glowing mushrooms, foggy atmosphere",
    "width": 1920,
    "height": 1080,
    "seed": 77777
})
```

### 4. Pixel Art (`pixel-art`)

**Purpose**: Generate pixel art style sprites and assets

**Dimensions**: 256×256 (optimized for pixel art)

**Parameters**:
- `prompt` (string, required) - Asset description
- `negative_prompt` (string) - Things to avoid
- `width` (int) - Image width (default: 256)
- `height` (int) - Image height (default: 256)
- `steps` (int) - Sampling steps (default: 20)
- `seed` (int) - Random seed (default: 42)

**Use Cases**:
- Retro game sprites
- Pixel art characters
- Tile sets
- UI elements for pixel art games

**Example**:
```python
workflow = template.instantiate({
    "prompt": "16-bit style dragon sprite, pixel art, game asset",
    "width": 64,
    "height": 64,
    "seed": 54321
})
```

---

## Parameter Substitution

### Placeholder Syntax

Parameters are substituted using the `{{parameter_name}}` syntax:

```json
{
  "class_type": "CLIPTextEncode",
  "inputs": {
    "text": "{{prompt}}, highly detailed, professional",
    "clip": ["1", 1]
  }
}
```

### Substitution Rules

**String Placeholders**:
```json
"text": "{{prompt}}"
→ "text": "fantasy warrior"
```

**Numeric Placeholders**:
```json
"width": "{{width}}"
→ "width": 512
```

**Entire Value Replacement**:
```json
"seed": "{{seed}}"
→ "seed": 42
```

**Partial String Replacement**:
```json
"text": "{{prompt}}, detailed face, portrait"
→ "text": "elf ranger, detailed face, portrait"
```

**Multiple Placeholders**:
```json
"text": "{{style}} {{prompt}} in {{environment}}"
→ "text": "fantasy elf ranger in mystical forest"
```

### Type Preservation

The substitution engine preserves types:

```python
# Integer parameter
{"seed": "{{seed}}"}  # Template
{"seed": 42}          # After substitution (int, not string)

# Float parameter
{"cfg": "{{cfg}}"}    # Template
{"cfg": 7.5}          # After substitution (float)

# String parameter
{"text": "{{prompt}}"}  # Template
{"text": "warrior"}     # After substitution (string)

# Boolean parameter
{"enabled": "{{use_lora}}"}  # Template
{"enabled": true}            # After substitution (bool)
```

### Nested Structures

Placeholders work in nested dictionaries and lists:

```python
nodes = {
    "5": WorkflowNode(
        class_type="KSampler",
        inputs={
            "seed": "{{seed}}",
            "steps": "{{steps}}",
            "cfg": "{{cfg}}",
            "model": ["1", 0],        # No placeholder - preserved as-is
            "positive": ["{{pos_node}}", 0]  # Placeholder in list
        }
    )
}
```

### Missing Parameters

If a parameter is not provided during instantiation:

1. **Has Default**: Uses the parameter's default value
2. **No Default**: Placeholder remains unreplaced (usually causes error)

```python
# Template defines: "prompt" with default "landscape"
workflow = template.instantiate({})
# Result: Uses "landscape" as prompt

# Template defines: "prompt" without default (required=True)
workflow = template.instantiate({})
# Result: May cause validation error or leave placeholder
```

---

## Template Manager

### WorkflowTemplateManager

The `WorkflowTemplateManager` class provides centralized template management:

```python
from comfyui_mcp import WorkflowTemplateManager

# Initialize with templates directory
manager = WorkflowTemplateManager(templates_dir="workflows/")
```

### Loading Templates

```python
# Load specific template by ID
template = manager.load_template("character-portrait")

# Load all templates
all_templates = manager.load_all_templates()

# Load with error handling
try:
    template = manager.load_template("custom-template")
except FileNotFoundError:
    print("Template not found")
except ValidationError as e:
    print(f"Invalid template: {e}")
```

### Discovering Templates

```python
# List all available templates
template_list = manager.list_templates()
for tmpl in template_list:
    print(f"{tmpl.name} ({tmpl.category}): {tmpl.description}")

# Find by category
character_templates = manager.find_by_category("character")
item_templates = manager.find_by_category("item")

# Search by name
results = manager.search("portrait")
```

### Saving Templates

```python
from comfyui_mcp import WorkflowTemplate, TemplateParameter, WorkflowNode

# Create new template
template = WorkflowTemplate(
    name="My Custom Template",
    description="Custom workflow for specific use case",
    category="custom",
    parameters={...},
    nodes={...}
)

# Save to file
manager.save_template(template, "my-custom-template")
# Saves to: workflows/my-custom-template.json
```

### Validating Templates

```python
# Validate template structure
is_valid = manager.validate_template(template)

# Validate with detailed errors
errors = manager.validate_template_detailed(template)
if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

### Template Metadata

```python
# Get template metadata without loading full template
metadata = manager.get_template_metadata("character-portrait")
print(f"Name: {metadata['name']}")
print(f"Category: {metadata['category']}")
print(f"Parameters: {len(metadata['parameters'])}")

# List all categories
categories = manager.get_categories()
# Returns: ["character", "item", "environment", "custom", ...]
```

---

## Best Practices

### 1. Naming Conventions

**Template Names**:
- Use descriptive, hyphen-separated names: `character-portrait`, `item-icon-hd`
- Include variant suffixes: `portrait-hd`, `portrait-sd`, `portrait-pixel`
- Be consistent across your template library

**Parameter Names**:
- Use lowercase with underscores: `prompt`, `negative_prompt`, `cfg_scale`
- Be explicit: `sampler_steps` not `steps`, `image_width` not `width`
- Match ComfyUI conventions where applicable

### 2. Parameter Defaults

**Choose Sensible Defaults**:
```python
TemplateParameter(
    name="steps",
    description="Sampling steps",
    type="int",
    default=25,  # Good balance of quality and speed
    required=False
)
```

**Document Ranges**:
```python
TemplateParameter(
    name="cfg",
    description="CFG scale (5.0-15.0, typically 7.0-8.0)",
    type="float",
    default=7.5,
    required=False
)
```

### 3. Template Organization

**Directory Structure**:
```
workflows/
├── core/              # Built-in templates
│   ├── character-portrait.json
│   ├── item-icon.json
│   └── environment-bg.json
├── game-specific/     # Project templates
│   ├── rpg-npc-portrait.json
│   └── platformer-sprite.json
└── experimental/      # WIP templates
    └── test-workflow.json
```

### 4. Documentation

**Template Description**:
```python
WorkflowTemplate(
    name="Character Portrait HD",
    description="""
    High-definition character portrait generator optimized for RPG games.

    Features:
    - Portrait orientation (512×768)
    - Enhanced face detail
    - Good for close-up character shots

    Best for:
    - NPC dialogue portraits
    - Character selection screens
    - Inventory character previews
    """,
    category="character",
    ...
)
```

**Parameter Documentation**:
```python
TemplateParameter(
    name="steps",
    description="Number of sampling steps. Higher = better quality but slower. Range: 15-50, recommended: 20-30.",
    type="int",
    default=25,
    required=False
)
```

### 5. Validation

**Validate Before Saving**:
```python
def create_template():
    template = WorkflowTemplate(...)

    # Validate structure
    try:
        workflow = template.instantiate({})
        print("Template validation passed")
    except Exception as e:
        print(f"Validation failed: {e}")
        return None

    return template
```

### 6. Version Control

**Track Template Changes**:
- Store templates in Git
- Use semantic versioning in filenames: `portrait-v2.json`
- Document breaking changes in commit messages
- Keep old versions for backward compatibility

### 7. Testing

**Test With Various Inputs**:
```python
test_cases = [
    {"prompt": "warrior", "seed": 1},
    {"prompt": "mage with staff", "seed": 2, "steps": 30},
    {"prompt": "rogue", "width": 768, "height": 768},
]

for params in test_cases:
    workflow = template.instantiate(params)
    # Verify workflow structure
    assert "1" in workflow.nodes
    assert workflow.nodes["2"].inputs["text"] != "{{prompt}}"
```

### 8. Performance Optimization

**Choose Appropriate Defaults**:
- `steps=20-25` for development/testing
- `steps=30-50` for production assets
- Lower dimensions for faster iteration
- Use batch generation for multiple assets

### 9. Error Handling

**Graceful Degradation**:
```python
try:
    template = manager.load_template("character-portrait")
    workflow = template.instantiate(params)
except FileNotFoundError:
    # Fallback to basic workflow
    template = manager.load_template("basic-generator")
    workflow = template.instantiate(params)
except ValidationError as e:
    print(f"Invalid parameters: {e}")
    # Use defaults
    workflow = template.instantiate({})
```

### 10. Reusability

**Create Base Templates**:
```python
# Base template with common settings
base_template = WorkflowTemplate(
    name="Base SD1.5 Generator",
    description="Base template for SD1.5 workflows",
    parameters=common_parameters,
    nodes=base_nodes
)

# Extend for specific uses
character_template = extend_template(
    base_template,
    name="Character Portrait",
    additional_nodes=portrait_specific_nodes
)
```

---

## Complete Examples

### Example 1: RPG Character Generator

Complete template for generating RPG character portraits with LoRA support:

```python
from comfyui_mcp import WorkflowTemplate, TemplateParameter, WorkflowNode

rpg_character_template = WorkflowTemplate(
    name="RPG Character Portrait",
    description="High-quality character portraits with fantasy art style LoRA",
    category="character",
    parameters={
        "prompt": TemplateParameter(
            name="prompt",
            description="Character description (class, appearance, equipment)",
            type="string",
            default="fantasy warrior",
            required=True
        ),
        "class": TemplateParameter(
            name="class",
            description="Character class (warrior, mage, rogue, cleric)",
            type="string",
            default="warrior",
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
            description="Sampling steps (20-50)",
            type="int",
            default=30,
            required=False
        ),
        "lora_strength": TemplateParameter(
            name="lora_strength",
            description="Fantasy art LoRA strength (0.0-1.0)",
            type="float",
            default=0.7,
            required=False
        )
    },
    nodes={
        "1": WorkflowNode(
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "v1-5-pruned.safetensors"}
        ),
        "2": WorkflowNode(
            class_type="LoraLoader",
            inputs={
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": "fantasy_rpg_style.safetensors",
                "strength_model": "{{lora_strength}}",
                "strength_clip": "{{lora_strength}}"
            }
        ),
        "3": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={
                "text": "{{prompt}}, {{class}}, detailed face, fantasy art, character portrait, professional",
                "clip": ["2", 1]
            }
        ),
        "4": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={
                "text": "blurry, low quality, deformed, ugly, bad anatomy, multiple people",
                "clip": ["2", 1]
            }
        ),
        "5": WorkflowNode(
            class_type="EmptyLatentImage",
            inputs={"width": 512, "height": 768, "batch_size": 1}
        ),
        "6": WorkflowNode(
            class_type="KSampler",
            inputs={
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
        ),
        "7": WorkflowNode(
            class_type="VAEDecode",
            inputs={"samples": ["6", 0], "vae": ["1", 2]}
        ),
        "8": WorkflowNode(
            class_type="SaveImage",
            inputs={
                "images": ["7", 0],
                "filename_prefix": "rpg_{{class}}_{{seed}}"
            }
        )
    }
)

# Usage
workflow = rpg_character_template.instantiate({
    "prompt": "female elf ranger with longbow",
    "class": "ranger",
    "seed": 12345,
    "steps": 35,
    "lora_strength": 0.8
})
```

### Example 2: Item Icon Batch Generator

Template optimized for generating multiple item icons efficiently:

```python
item_icon_template = WorkflowTemplate(
    name="Item Icon Generator",
    description="Centered item icons for inventory systems",
    category="item",
    parameters={
        "item_type": TemplateParameter(
            name="item_type",
            description="Type of item (weapon, potion, armor, resource)",
            type="string",
            default="weapon",
            required=True
        ),
        "description": TemplateParameter(
            name="description",
            description="Item description",
            type="string",
            default="iron sword",
            required=True
        ),
        "rarity": TemplateParameter(
            name="rarity",
            description="Item rarity (common, rare, epic, legendary)",
            type="string",
            default="common",
            required=False
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
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "v1-5-pruned.safetensors"}
        ),
        "2": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={
                "text": "{{description}}, {{rarity}} {{item_type}}, game icon, centered, simple background, high detail, isometric view",
                "clip": ["1", 1]
            }
        ),
        "3": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={
                "text": "blurry, low quality, hands, people, text, watermark, multiple items",
                "clip": ["1", 1]
            }
        ),
        "4": WorkflowNode(
            class_type="EmptyLatentImage",
            inputs={"width": 512, "height": 512, "batch_size": 1}
        ),
        "5": WorkflowNode(
            class_type="KSampler",
            inputs={
                "seed": "{{seed}}",
                "steps": 20,
                "cfg": 8.0,
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
            inputs={
                "images": ["6", 0],
                "filename_prefix": "item_{{item_type}}_{{rarity}}_{{seed}}"
            }
        )
    }
)

# Batch generation example
items = [
    {"item_type": "weapon", "description": "iron sword", "rarity": "common", "seed": 1},
    {"item_type": "weapon", "description": "flaming sword", "rarity": "rare", "seed": 2},
    {"item_type": "potion", "description": "health potion", "rarity": "common", "seed": 3},
    {"item_type": "armor", "description": "leather armor", "rarity": "common", "seed": 4},
]

workflows = [item_icon_template.instantiate(params) for params in items]
```

### Example 3: Environment Background with Variations

Template for generating environment backgrounds with style variations:

```python
environment_template = WorkflowTemplate(
    name="Environment Background",
    description="Wide-angle environment backgrounds for game levels",
    category="environment",
    parameters={
        "scene": TemplateParameter(
            name="scene",
            description="Scene description",
            type="string",
            default="forest landscape",
            required=True
        ),
        "time_of_day": TemplateParameter(
            name="time_of_day",
            description="Time of day (dawn, day, dusk, night)",
            type="string",
            default="day",
            required=False
        ),
        "weather": TemplateParameter(
            name="weather",
            description="Weather condition (clear, rain, fog, snow)",
            type="string",
            default="clear",
            required=False
        ),
        "style": TemplateParameter(
            name="style",
            description="Art style (realistic, fantasy, sci-fi, pixel art)",
            type="string",
            default="fantasy",
            required=False
        ),
        "width": TemplateParameter(
            name="width",
            description="Image width",
            type="int",
            default=1024,
            required=False
        ),
        "height": TemplateParameter(
            name="height",
            description="Image height",
            type="int",
            default=576,
            required=False
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
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "v1-5-pruned.safetensors"}
        ),
        "2": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={
                "text": "{{scene}}, {{time_of_day}}, {{weather}}, {{style}} art, wide angle, landscape, environment art, detailed background",
                "clip": ["1", 1]
            }
        ),
        "3": WorkflowNode(
            class_type="CLIPTextEncode",
            inputs={
                "text": "people, characters, faces, blurry, low quality, text, watermark",
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
        ),
        "6": WorkflowNode(
            class_type="VAEDecode",
            inputs={"samples": ["5", 0], "vae": ["1", 2]}
        ),
        "7": WorkflowNode(
            class_type="SaveImage",
            inputs={
                "images": ["6", 0],
                "filename_prefix": "env_{{time_of_day}}_{{weather}}_{{seed}}"
            }
        )
    }
)

# Generate variations
variations = [
    {"scene": "mystical forest", "time_of_day": "dawn", "weather": "fog", "seed": 1},
    {"scene": "mystical forest", "time_of_day": "day", "weather": "clear", "seed": 2},
    {"scene": "mystical forest", "time_of_day": "dusk", "weather": "clear", "seed": 3},
    {"scene": "mystical forest", "time_of_day": "night", "weather": "clear", "seed": 4},
]

workflows = [environment_template.instantiate(params) for params in variations]
```

---

## Advanced Topics

### Custom Parameter Types

While the system supports basic types, you can encode complex types as strings:

```python
# JSON-encoded array parameter
TemplateParameter(
    name="lora_list",
    description="List of LoRA models as JSON array",
    type="string",
    default='["fantasy.safetensors", "detailed.safetensors"]',
    required=False
)

# Usage
import json
lora_list = json.loads(params["lora_list"])
```

### Conditional Logic in Templates

Implement conditional logic through parameter values:

```python
# Template with conditional LoRA loading
parameters = {
    "use_lora": TemplateParameter(
        name="use_lora",
        description="Whether to use LoRA enhancement",
        type="bool",
        default=False,
        required=False
    ),
    "lora_name": TemplateParameter(
        name="lora_name",
        description="LoRA model filename",
        type="string",
        default="fantasy_style.safetensors",
        required=False
    )
}

# In application code, conditionally build workflow
if params.get("use_lora", False):
    workflow_with_lora = add_lora_nodes(base_workflow, params["lora_name"])
else:
    workflow_with_lora = base_workflow
```

### Template Inheritance

Create specialized templates from base templates:

```python
def create_specialized_template(base_template, overrides):
    """Create a specialized version of a base template."""
    specialized_nodes = base_template.nodes.copy()
    specialized_nodes.update(overrides.get("nodes", {}))

    specialized_params = base_template.parameters.copy()
    specialized_params.update(overrides.get("parameters", {}))

    return WorkflowTemplate(
        name=overrides.get("name", base_template.name),
        description=overrides.get("description", base_template.description),
        category=overrides.get("category", base_template.category),
        parameters=specialized_params,
        nodes=specialized_nodes
    )

# Use
hd_portrait_template = create_specialized_template(
    character_portrait_template,
    {
        "name": "HD Character Portrait",
        "parameters": {
            "width": TemplateParameter(
                name="width",
                description="Image width",
                type="int",
                default=1024,  # Override default
                required=False
            )
        }
    }
)
```

### Template Composition

Combine multiple templates into complex workflows:

```python
def compose_templates(templates, connections):
    """Compose multiple templates into a single workflow."""
    combined_nodes = {}
    combined_params = {}
    node_offset = 0

    for i, template in enumerate(templates):
        # Offset node IDs to avoid conflicts
        for node_id, node in template.nodes.items():
            new_id = str(int(node_id) + node_offset)
            combined_nodes[new_id] = node

        # Merge parameters
        combined_params.update(template.parameters)
        node_offset += 100

    # Apply connections between templates
    for connection in connections:
        from_node = str(connection["from"])
        to_node = str(connection["to"])
        combined_nodes[to_node].inputs[connection["input"]] = [from_node, connection["output"]]

    return WorkflowTemplate(
        name="Composed Workflow",
        description="Multi-stage workflow",
        category="advanced",
        parameters=combined_params,
        nodes=combined_nodes
    )
```

### Dynamic Template Generation

Generate templates programmatically:

```python
def generate_batch_template(base_workflow, batch_size):
    """Generate a template for batch processing."""
    nodes = base_workflow.nodes.copy()

    # Modify EmptyLatentImage node for batch processing
    for node_id, node in nodes.items():
        if node.class_type == "EmptyLatentImage":
            node.inputs["batch_size"] = batch_size

    return WorkflowTemplate(
        name=f"Batch Generator (x{batch_size})",
        description=f"Generate {batch_size} images in parallel",
        category="batch",
        parameters=base_workflow.parameters,
        nodes=nodes
    )
```

---

## Troubleshooting

### Common Issues

**1. Placeholder Not Replaced**

**Symptom**: `{{parameter_name}}` appears in final workflow

**Causes**:
- Parameter name mismatch
- Parameter not provided and no default
- Typo in placeholder name

**Solution**:
```python
# Check parameter names match
template.parameters.keys()  # ['prompt', 'seed', 'steps']

# Ensure parameter is provided or has default
workflow = template.instantiate({"prompt": "test", "seed": 42})
```

**2. Type Error During Instantiation**

**Symptom**: `TypeError: invalid type for parameter`

**Cause**: Parameter value doesn't match declared type

**Solution**:
```python
# Correct types
params = {
    "steps": 25,        # int
    "cfg": 7.5,         # float
    "prompt": "text",   # string
    "enabled": True     # bool
}

# Wrong types
params = {
    "steps": "25",      # Should be int, not string
    "cfg": "7.5",       # Should be float, not string
}
```

**3. Node Connection Errors**

**Symptom**: `Node connection failed: invalid node ID`

**Cause**: Placeholder in node connection not replaced

**Solution**:
```python
# Don't use placeholders in connections
# Wrong:
"model": ["{{model_node}}", 0]

# Correct:
"model": ["1", 0]
```

**4. Template Not Found**

**Symptom**: `FileNotFoundError: template not found`

**Cause**: Template file doesn't exist or wrong path

**Solution**:
```python
manager = WorkflowTemplateManager(templates_dir="workflows/")

# Check available templates
templates = manager.list_templates()
print([t.name for t in templates])

# Use correct template ID
template = manager.load_template("character-portrait")  # Matches filename
```

---

## Conclusion

The workflow template system provides a robust, scalable approach to image generation with ComfyUI. By understanding template structure, parameter substitution, and best practices, you can create efficient, reusable workflows for any game asset generation task.

### Key Takeaways

✅ **Templates encapsulate workflows** with configurable parameters
✅ **Parameter substitution** uses `{{placeholder}}` syntax
✅ **WorkflowTemplateManager** provides centralized template management
✅ **Built-in templates** cover common game asset types
✅ **Best practices** ensure maintainable, efficient templates
✅ **Advanced features** support complex workflows and composition

### Next Steps

1. **Explore built-in templates** - Try the 4 standard templates
2. **Create custom templates** - Build templates for your specific needs
3. **Integrate with MCP** - Use templates via `generate_image` MCP tool
4. **Build template libraries** - Organize templates by project/game
5. **Contribute templates** - Share templates with the community

### Additional Resources

- **[Workflow Creation Tutorial](WORKFLOW_TUTORIAL.md)** - Learn to create ComfyUI workflows
- **[MCP Tool Usage](MCP_TOOLS.md)** - Use templates via MCP server
- **[API Documentation](API.md)** - Python API reference
- **[README](../README.md)** - Project overview and quick start

### Getting Help

- **[GitHub Issues](https://github.com/PurlieuStudios/comfyui-mcp/issues)** - Report bugs or request features
- **[GitHub Discussions](https://github.com/PurlieuStudios/comfyui-mcp/discussions)** - Ask questions and share templates

---

**Version:** 1.0.0
**Last Updated:** 2025-01-18
**Maintainer:** [Purlieu Studios](https://purlieu.studio)
