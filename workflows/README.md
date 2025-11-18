# ComfyUI Workflow Templates

This directory contains workflow templates for generating game assets with ComfyUI.

Workflow templates are reusable JSON files that define ComfyUI workflows with customizable parameters. They enable consistent, reproducible image generation for game development.

## Available Templates

### Character Assets
- **`character-portrait.json`** - Generate character portraits for RPGs (512x512)
  - Optimized for character cards, dialogue boxes, and inventory screens
  - Customizable prompt, seed, steps, and CFG scale

### Item Assets
- **`item-icon.json`** - Generate item icons for inventories (512x512, centered)
  - Perfect for weapons, potions, equipment, and collectibles
  - Supports custom backgrounds and item descriptions

### Environment Assets
- `environment-texture.json` *(coming soon)* - Generate tileable environment textures

### Specialized
- `pixel-art.json` *(coming soon)* - Pixel art generation with upscale + pixelate

## Template File Format

Each template is a JSON file following this structure:

```json
{
  "name": "Template Name",
  "description": "What this template generates",
  "category": "character|item|environment|specialized",
  "parameters": {
    "param_name": {
      "name": "param_name",
      "description": "Parameter description",
      "type": "string|int|float|bool",
      "default": "default_value",
      "required": true
    }
  },
  "nodes": {
    "node_id": {
      "class_type": "ComfyUI Node Type",
      "inputs": {
        "input_name": "{{param_name}}",
        "connection": ["other_node_id", output_slot]
      }
    }
  }
}
```

### Template Fields

- **`name`** (required): Human-readable template name
- **`description`** (required): Detailed description of what the template generates
- **`category`** (optional): One of: `character`, `item`, `environment`, `specialized`, or `null`
- **`parameters`** (required): Dictionary of customizable parameters
- **`nodes`** (required): ComfyUI workflow node graph

### Parameter Definition

Each parameter has the following structure:

```json
{
  "name": "parameter_name",
  "description": "What this parameter controls",
  "type": "string|int|float|bool",
  "default": "default_value",
  "required": true
}
```

- **`name`**: Must match the placeholder used in nodes (e.g., `{{param_name}}`)
- **`description`**: Help text explaining the parameter's purpose
- **`type`**: Data type (`string`, `int`, `float`, or `bool`)
- **`default`**: Default value if not specified
- **`required`**: Whether the parameter must be provided (`true` or `false`)

### Node Structure

Nodes follow the ComfyUI format:

```json
{
  "class_type": "NodeClassName",
  "inputs": {
    "param1": "value",
    "param2": "{{placeholder}}",
    "connection": ["source_node_id", output_slot_index]
  }
}
```

- **`class_type`**: ComfyUI node type (e.g., `KSampler`, `CLIPTextEncode`)
- **`inputs`**: Node parameters and connections
  - Use `{{param_name}}` for template parameter substitution
  - Use `["node_id", slot]` arrays for node connections

## Using Templates in Code

### Python API

```python
from comfyui_mcp import WorkflowTemplate

# Load a template
template = WorkflowTemplate.from_file("workflows/character-portrait.json")

# Instantiate with custom parameters
workflow = template.instantiate({
    "prompt": "a wizard with blue robes",
    "seed": 42,
    "steps": 30
})

# Use with ComfyUI client
async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)
```

### Creating New Templates

1. **Design in ComfyUI**
   - Create your workflow in the ComfyUI web interface
   - Test it with various inputs to ensure it works

2. **Export the Workflow**
   - Export the workflow JSON from ComfyUI
   - Note the node IDs and structure

3. **Add Template Metadata**
   ```json
   {
     "name": "My Custom Template",
     "description": "Generates custom game assets",
     "category": "specialized",
     "parameters": { ... },
     "nodes": { ... }
   }
   ```

4. **Add Parameter Placeholders**
   - Replace hardcoded values with `{{param_name}}` placeholders
   - Define each parameter in the `parameters` section

5. **Validate the Template**
   ```python
   # Load and test your template
   template = WorkflowTemplate.from_file("workflows/my-template.json")

   # Verify it instantiates correctly
   workflow = template.instantiate({"param1": "value"})
   ```

6. **Save and Test**
   ```python
   # Save programmatically
   template.to_file("workflows/my-template.json")
   ```

## JSON Schema Validation

Templates can be validated against the JSON Schema at `../schemas/workflow-template.schema.json`.

This ensures:
- All required fields are present
- Field types are correct
- Parameter definitions are complete
- Node structures are valid

## Best Practices

### Parameter Naming
- Use descriptive names: `character_class` instead of `char`
- Follow snake_case convention: `cfg_scale`, `num_steps`
- Match placeholder names: If the parameter is `prompt`, use `{{prompt}}`

### Default Values
- Choose sensible defaults that work for most cases
- For seeds, use `-1` to indicate random generation
- For steps, balance quality (20-30) with speed

### Node Organization
- Number nodes logically (1 = loader, 2-3 = encoders, 4 = latent, 5 = sampler, etc.)
- Group related nodes together
- Use clear, sequential IDs

### Documentation
- Write clear, detailed descriptions for both templates and parameters
- Include examples in parameter descriptions
- Explain what different parameter values do

## Template Categories

### Character Templates
Generate character-related assets: portraits, sprites, expressions, variations

**Best for**: RPGs, visual novels, character-driven games

### Item Templates
Generate item icons and equipment visuals

**Best for**: Inventory systems, loot, collectibles

### Environment Templates
Generate backgrounds, textures, and environmental elements

**Best for**: Platformers, tile-based games, scene backgrounds

### Specialized Templates
Custom workflows for specific use cases (pixel art, batch processing, etc.)

**Best for**: Unique requirements not covered by other categories

## Contributing Templates

When adding new templates to this repository:

1. Follow the file format exactly
2. Include comprehensive parameter descriptions
3. Test the template with various parameter values
4. Add the template to this README's template list
5. Include usage examples in the template description

## Resources

- **JSON Schema**: `../schemas/workflow-template.schema.json`
- **API Documentation**: `../docs/API.md`
- **Workflow Tutorial**: `../docs/WORKFLOW_TUTORIAL.md`
- **ComfyUI Docs**: https://github.com/comfyanonymous/ComfyUI

## Troubleshooting

### Template Won't Load
- Validate JSON syntax (use a JSON linter)
- Check that all required fields are present
- Ensure parameter names match placeholders
- Verify node IDs are unique strings

### Parameter Substitution Not Working
- Check placeholder format: `{{param_name}}` (double braces)
- Ensure parameter name matches exactly (case-sensitive)
- Verify the parameter is defined in the `parameters` section

### Node Connections Failing
- Verify node IDs exist
- Check output slot indices (usually 0, 1, or 2)
- Ensure connection format: `["node_id", slot_number]`

---

For more detailed information on creating and using workflow templates, see the [Workflow Creation Tutorial](../docs/WORKFLOW_TUTORIAL.md).
