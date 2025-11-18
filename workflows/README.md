# ComfyUI Workflow Templates

This directory contains workflow templates for generating game assets with ComfyUI.

## Template Categories

### Character Assets
- `character-portrait.json` - Generate character portraits for RPGs
- `sprite-variations.json` - Create sprite variations

### Item Assets
- `item-icon.json` - Generate item icons (512x512, centered)

### Environment Assets
- `environment-texture.json` - Generate tileable environment textures

### Specialized
- `pixel-art.json` - Pixel art generation with upscale + pixelate

## Template Format

Each template is a JSON file with the following structure:

```json
{
  "name": "Template Name",
  "description": "What this template generates",
  "category": "character|item|environment|specialized",
  "parameters": {
    "prompt": {"type": "string", "default": "default prompt"},
    "width": {"type": "int", "default": 512},
    "height": {"type": "int", "default": 512},
    "seed": {"type": "int", "default": -1}
  },
  "workflow": {
    // ComfyUI workflow nodes
  }
}
```

## Creating Custom Templates

1. Create your workflow in ComfyUI
2. Export the workflow JSON
3. Add parameter placeholders (e.g., `{{prompt}}`, `{{width}}`)
4. Add metadata (name, description, category, parameters)
5. Test the template with the MCP server
