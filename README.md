# ComfyUI MCP Server

> AI-powered image generation for Godot game development via ComfyUI

[![CI](https://github.com/purlieu-studios/comfyui-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/purlieu-studios/comfyui-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

ComfyUI MCP Server is a Model Context Protocol (MCP) server that bridges [ComfyUI](https://github.com/comfyanonymous/ComfyUI)'s workflow-based AI image generation with [Godot](https://godotengine.org/) game development. Generate game assets dynamically during development or runtime.

### Features

- **MCP Integration**: Expose ComfyUI workflows as MCP tools
- **Workflow Templates**: Pre-built templates for common game assets
- **Async Operations**: Non-blocking generation with real-time progress updates
- **Godot Support**: Seamless integration with Godot 3.x and 4.x
- **Flexible Configuration**: Environment variables and config files

### Use Cases

- **Character Generation**: NPC portraits, character sprites
- **Item Icons**: Unique item icons based on descriptions
- **Environment Art**: Background textures, tileable patterns
- **Dynamic Content**: Procedural asset generation on-the-fly
- **Concept Art**: Rapid prototyping and visual development

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installed and running on `http://127.0.0.1:8188`
- Stable Diffusion models downloaded and available in ComfyUI

### Installation

```bash
# Clone the repository
git clone https://github.com/purlieu-studios/comfyui-mcp.git
cd comfyui-mcp

# Install the package
pip install -e .

# For development
pip install -e ".[dev]"
```

### Configuration

Create or update your `.mcp.json` configuration file:

```json
{
  "mcpServers": {
    "comfyui-mcp": {
      "command": "python",
      "args": ["-m", "comfyui_mcp.server"],
      "env": {
        "COMFYUI_URL": "http://127.0.0.1:8188",
        "COMFYUI_OUTPUT_DIR": "path/to/comfyui/output"
      }
    }
  }
}
```

### Usage

#### MCP Tools

- `generate_image`: Generate images using ComfyUI workflows
- `list_workflows`: List available workflow templates
- `get_workflow_status`: Check the status of a running workflow
- `cancel_workflow`: Cancel a running workflow
- `load_workflow`: Load a custom workflow from file

#### Example: Generate Character Portrait

```python
# Via Claude Code or MCP client
result = await mcp.call_tool(
    "generate_image",
    {
        "template": "character-portrait",
        "prompt": "fantasy elf warrior, detailed armor",
        "width": 512,
        "height": 512
    }
)
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v --cov=comfyui_mcp

# Run type checking
mypy src/

# Run linting
ruff check src/ tests/

# Format code
ruff format src/ tests/
black src/ tests/
```

### Project Structure

```
comfyui-mcp/
├── src/
│   └── comfyui_mcp/        # Main package
│       ├── __init__.py
│       ├── server.py       # MCP server implementation
│       ├── comfyui_client.py  # ComfyUI API client
│       ├── models.py       # Pydantic data models
│       └── ...
├── tests/                  # Test suite
├── examples/               # Godot integration examples
├── workflows/              # Workflow templates
├── .github/workflows/      # CI/CD configuration
├── pyproject.toml          # Package configuration
└── README.md
```

## Documentation

- [Quick Start Guide](docs/quick-start.md) *(coming soon)*
- [Godot Integration Guide](docs/godot-integration.md) *(coming soon)*
- [Workflow Template Format](docs/workflow-templates.md) *(coming soon)*
- [API Documentation](docs/api.md) *(coming soon)*
- [Contributing Guide](CONTRIBUTING.md) *(coming soon)*

## Workflow Templates

Pre-built templates for common game assets:

- **character-portrait**: Character portraits for RPGs (SD 1.5 base)
- **item-icon**: Item icons (512x512, centered)
- **environment-texture**: Tileable environment textures
- **pixel-art**: Pixel art generation (upscale + pixelate)

See [workflows/](workflows/) directory for template files.

## Examples

Explore [examples/](examples/) for Godot integration samples:

- Character portrait generation for RPG
- Item icon batch generation
- Environment texture generation
- Real-time generation in Godot
- Procedural sprite variation

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and quality checks
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - Powerful workflow-based Stable Diffusion UI
- [Godot Engine](https://godotengine.org/) - Open-source game engine
- [Model Context Protocol](https://modelcontextprotocol.io/) - Universal AI integration standard

## Support

- **Issues**: [GitHub Issues](https://github.com/purlieu-studios/comfyui-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/purlieu-studios/comfyui-mcp/discussions)

## Roadmap

See [CHANGELOG.md](CHANGELOG.md) and [GitHub Milestones](https://github.com/purlieu-studios/comfyui-mcp/milestones) for upcoming features.

---

**Status**: Alpha - Active Development

Built with by [Purlieu Studios](https://purlieu.studio)
