# ComfyUI MCP Server

> AI-powered image generation for game development via ComfyUI and the Model Context Protocol

[![CI](https://github.com/purlieu-studios/comfyui-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/purlieu-studios/comfyui-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

## Overview

ComfyUI MCP Server is a **Model Context Protocol (MCP) server** that bridges [ComfyUI](https://github.com/comfyanonymous/ComfyUI)'s powerful workflow-based AI image generation with modern development workflows. Originally designed for [Godot](https://godotengine.org/) game development, it can be used with any MCP-compatible client to generate game assets, concept art, and visual content dynamically.

### Key Features

- **MCP Integration**: Expose ComfyUI workflows as standardized MCP tools
- **Python API Client**: Full-featured async ComfyUI API client with type safety
- **Workflow Templates**: Pre-built templates for common game assets (characters, items, environments)
- **Async Operations**: Non-blocking generation with real-time progress updates via WebSockets
- **Flexible Configuration**: TOML files, environment variables, or Python code
- **Type Safe**: Full type hints with strict mypy validation
- **Well Tested**: Comprehensive test coverage with pytest
- **Production Ready**: Retry logic, error handling, and logging built-in

### Use Cases

- **Character Generation**: NPC portraits, character sprites, concept art
- **Item Icons**: Unique item icons from text descriptions
- **Environment Art**: Background textures, tileable patterns, landscapes
- **Dynamic Content**: Procedural asset generation during gameplay
- **Concept Art**: Rapid visual prototyping and iteration
- **Batch Processing**: Generate multiple asset variations efficiently

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [MCP Server](#mcp-server-usage)
  - [Python API Client](#python-api-client)
- [Workflow Templates](#workflow-templates)
- [Documentation](#documentation)
- [Examples](#examples)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

### Prerequisites

1. **Python 3.10 or higher**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **ComfyUI installed and running**
   - Download: [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
   - Default URL: `http://localhost:8188`
   - Verify: Open `http://localhost:8188` in your browser

3. **Stable Diffusion models**
   - Download models and place in ComfyUI's `models/checkpoints/` directory
   - Recommended: Stable Diffusion 1.5 or 2.1 for game assets

### Installation

```bash
# Clone the repository
git clone https://github.com/purlieu-studios/comfyui-mcp.git
cd comfyui-mcp

# Install the package
pip install -e .

# For development (includes testing and linting tools)
pip install -e ".[dev]"

# Verify installation
python -c "from comfyui_mcp import ComfyUIClient; print('Installation successful!')"
```

### Basic Configuration

**Option 1: Environment Variables (Recommended for getting started)**

```bash
# Required
export COMFYUI_URL="http://localhost:8188"

# Optional
export COMFYUI_TIMEOUT="120.0"
export COMFYUI_OUTPUT_DIR="./generated_images"
```

**Option 2: TOML Configuration File**

Create `comfyui.toml` in your project root:

```toml
[comfyui]
url = "http://localhost:8188"
timeout = 120.0
output_dir = "./generated_images"
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for comprehensive configuration options.

### Your First Generation

#### Using the Python API

```python
import asyncio
from comfyui_mcp import ComfyUIClient, ComfyUIConfig, WorkflowPrompt

async def generate_image():
    # Configure the client
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        # Check ComfyUI server health
        if not await client.health_check():
            print("ComfyUI server is not responding!")
            return

        # Create a simple workflow
        workflow = WorkflowPrompt(
            prompt={
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": 42,
                        "steps": 20,
                        "cfg": 7.0,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0
                    }
                }
            }
        )

        # Submit and wait for completion
        prompt_id = await client.submit_workflow(workflow)
        print(f"Workflow submitted: {prompt_id}")

        result = await client.wait_for_completion(
            prompt_id=prompt_id,
            poll_interval=1.0,
            timeout=300.0
        )

        print(f"Generation complete! Result: {result}")

# Run the async function
asyncio.run(generate_image())
```

#### Using the MCP Server

**1. Configure MCP Server**

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "comfyui-mcp": {
      "command": "python",
      "args": ["-m", "comfyui_mcp.server"],
      "env": {
        "COMFYUI_URL": "http://localhost:8188",
        "COMFYUI_OUTPUT_DIR": "./generated_images"
      }
    }
  }
}
```

**2. Use via Claude Code or MCP Client**

```python
# Via MCP client (example)
result = await mcp.call_tool(
    "generate_image",
    {
        "template": "character-portrait",
        "prompt": "fantasy elf warrior with detailed armor and glowing sword",
        "width": 512,
        "height": 512,
        "steps": 25,
        "seed": 12345
    }
)
```

---

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/purlieu-studios/comfyui-mcp.git
cd comfyui-mcp

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### From PyPI (Coming Soon)

```bash
pip install comfyui-mcp
```

### Dependencies

**Core:**
- Python 3.10+
- `aiohttp` - Async HTTP client for ComfyUI API
- `pydantic` - Data validation and settings management
- `tomli` - TOML configuration file parsing
- `websockets` - WebSocket support for real-time updates

**Development:**
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `mypy` - Static type checking
- `ruff` - Fast linting and formatting
- `pre-commit` - Git hooks for code quality

---

## Configuration

ComfyUI MCP Server supports three configuration methods:

### 1. TOML Configuration File (Recommended for Projects)

Create `comfyui.toml`:

```toml
[comfyui]
# Required: ComfyUI server URL
url = "http://localhost:8188"

# Optional: API key for authentication (8+ characters)
# api_key = "your-api-key-here"

# Optional: Request timeout in seconds (1.0 - 3600.0)
timeout = 120.0

# Optional: Output directory for generated images
output_dir = "./generated_images"
```

**Configuration file locations** (searched in order):
1. `./comfyui.toml` (current directory)
2. `~/.config/comfyui/comfyui.toml` (user config)
3. `/etc/comfyui/comfyui.toml` (system-wide)

### 2. Environment Variables (Recommended for Deployment)

```bash
export COMFYUI_URL="http://localhost:8188"
export COMFYUI_API_KEY="your-api-key-min-8-chars"
export COMFYUI_TIMEOUT="120.0"
export COMFYUI_OUTPUT_DIR="./generated_images"
```

### 3. Python Code (Programmatic Configuration)

```python
from comfyui_mcp import ComfyUIConfig, ComfyUIClient

# Direct instantiation
config = ComfyUIConfig(
    url="http://localhost:8188",
    api_key="your-api-key",
    timeout=120.0,
    output_dir="./generated_images"
)

# Load from environment
config = ComfyUIConfig.from_env()

# Use the config
async with ComfyUIClient(config) as client:
    await client.health_check()
```

### Configuration Priority

When multiple methods are used:
1. **Python code** (highest priority)
2. **Environment variables**
3. **TOML configuration file**
4. **Default values** (lowest priority)

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for comprehensive configuration documentation.

---

## Usage

### MCP Server Usage

The MCP server exposes ComfyUI functionality as standardized MCP tools.

#### Available MCP Tools

| Tool | Description |
|------|-------------|
| `generate_image` | Generate images using workflow templates |
| `list_workflows` | List available workflow templates |
| `get_workflow_status` | Check generation progress and status |
| `cancel_workflow` | Cancel a running workflow |
| `load_workflow` | Load and use a custom workflow file |

#### Example: Generate Image Tool

```json
{
  "tool": "generate_image",
  "arguments": {
    "template": "character-portrait",
    "prompt": "cyberpunk hacker, neon lights, detailed face",
    "negative_prompt": "blurry, low quality",
    "width": 512,
    "height": 768,
    "steps": 30,
    "cfg_scale": 7.5,
    "seed": 42
  }
}
```

#### Starting the MCP Server

```bash
# Via Python module
python -m comfyui_mcp.server

# Or with custom configuration
COMFYUI_URL="http://localhost:8188" python -m comfyui_mcp.server
```

### Python API Client

Direct programmatic access to ComfyUI API.

#### Basic Usage

```python
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

async def main():
    config = ComfyUIConfig(url="http://localhost:8188")

    async with ComfyUIClient(config) as client:
        # Health check
        is_healthy = await client.health_check()
        print(f"ComfyUI Status: {'Online' if is_healthy else 'Offline'}")

        # Get system info
        system_stats = await client.get_system_stats()
        print(f"System: {system_stats}")
```

#### Submitting Workflows

```python
from comfyui_mcp import WorkflowPrompt

async def generate():
    config = ComfyUIConfig.from_env()

    async with ComfyUIClient(config) as client:
        workflow = WorkflowPrompt(
            prompt={
                "1": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "sd_v1-5.safetensors"}
                },
                "2": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": "beautiful landscape, mountains, sunset",
                        "clip": ["1", 0]
                    }
                }
                # ... more nodes
            }
        )

        # Submit workflow
        prompt_id = await client.submit_workflow(workflow)

        # Wait for completion (with polling)
        result = await client.wait_for_completion(
            prompt_id=prompt_id,
            poll_interval=2.0,  # Check every 2 seconds
            timeout=300.0        # Timeout after 5 minutes
        )

        return result
```

#### Queue Management

```python
async def manage_queue():
    async with ComfyUIClient(config) as client:
        # Get queue status
        queue = await client.get_queue()
        print(f"Queue size: {queue['queue_running']}")

        # Cancel specific workflow
        await client.cancel_workflow(prompt_id="abc-123")

        # Clear entire queue (careful!)
        await client.interrupt()
```

#### Retrieving Generated Images

```python
async def download_images(prompt_id: str):
    async with ComfyUIClient(config) as client:
        # Get workflow result
        history = await client.get_history(prompt_id)

        # Extract image filenames
        for node_id, output in history["outputs"].items():
            if "images" in output:
                for image in output["images"]:
                    # Download image
                    image_data = await client.download_image(
                        filename=image["filename"],
                        subfolder=image.get("subfolder", ""),
                        folder_type=image.get("type", "output")
                    )

                    # Save to file
                    with open(f"./output/{image['filename']}", "wb") as f:
                        f.write(image_data)
```

#### Error Handling

```python
from comfyui_mcp.exceptions import (
    ComfyUIError,
    ConnectionError,
    WorkflowExecutionError,
    TimeoutError
)

async def safe_generation():
    try:
        async with ComfyUIClient(config) as client:
            result = await client.submit_workflow(workflow)

    except ConnectionError as e:
        print(f"Cannot connect to ComfyUI: {e}")
    except WorkflowExecutionError as e:
        print(f"Workflow failed: {e}")
    except TimeoutError as e:
        print(f"Generation timed out: {e}")
    except ComfyUIError as e:
        print(f"ComfyUI error: {e}")
```

See [docs/API.md](docs/API.md) for complete API documentation.

---

## Workflow Templates

Pre-built workflow templates for common game asset types.

### Available Templates

| Template | Description | Size | Use Case |
|----------|-------------|------|----------|
| `character-portrait` | Character portraits and avatars | 512x512 | RPG character art, NPC portraits |
| `item-icon` | Centered item icons | 512x512 | Inventory items, UI icons |
| `environment-texture` | Tileable environment textures | 1024x1024 | Backgrounds, terrain textures |
| `pixel-art` | Upscaled pixel art style | 256x256 | Retro games, pixel art assets |

### Using Templates

```python
from comfyui_mcp import WorkflowTemplateManager

# Load template manager
manager = WorkflowTemplateManager(templates_dir="./workflows")

# List available templates
templates = manager.list_templates()
for template in templates:
    print(f"{template.name}: {template.description}")

# Load and customize template
template = manager.load_template("character-portrait")
workflow = template.instantiate(
    prompt="fantasy wizard with blue robes",
    seed=12345,
    steps=25
)

# Submit to ComfyUI
async with ComfyUIClient(config) as client:
    prompt_id = await client.submit_workflow(workflow)
```

### Creating Custom Templates

See [docs/workflow-templates.md](docs/workflow-templates.md) for template creation guide.

---

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[API Reference](docs/API.md)** - Complete Python API documentation
  - ComfyUIClient methods and parameters
  - Pydantic models and data structures
  - Exception handling
  - Type hints and examples

- **[Configuration Guide](docs/CONFIGURATION.md)** - Configuration options and best practices
  - TOML file format and schema
  - Environment variables
  - Configuration priority
  - Example configurations

- **[ComfyUI API Integration](docs/COMFYUI_API.md)** - ComfyUI REST API patterns
  - API endpoints and methods
  - Workflow structure
  - Queue management
  - WebSocket integration

- **[MCP Tool Usage](docs/MCP_TOOLS.md)** - Complete MCP tool reference and usage guide
  - All 5 MCP tools documented
  - Integration patterns and examples
  - Best practices and troubleshooting

- **[Workflow Creation Tutorial](docs/WORKFLOW_TUTORIAL.md)** - Comprehensive guide to creating ComfyUI workflows
  - Understanding workflow structure and node system
  - Creating workflows from scratch
  - Parameter substitution and templates
  - Advanced techniques (LoRA, ControlNet, batching)
  - Integration with MCP server
  - Complete examples for characters, items, and environments

- **[Workflow Template System](docs/WORKFLOW_TEMPLATES.md)** - Complete workflow template system documentation
  - Template structure and file format
  - Creating and using templates
  - Built-in templates (character, item, environment, pixel art)
  - Parameter substitution engine
  - WorkflowTemplateManager usage
  - Best practices and advanced topics
  - Complete examples and troubleshooting

- **[Godot Integration](docs/godot-integration.md)** *(coming soon)* - Godot plugin and examples

---

## Examples

Practical examples are available in the `examples/` directory:

### Example Projects

- **[Character Portrait Generation](examples/character_portrait.py)** - Generate RPG character portraits
- **[Item Icon Batch Generation](examples/item_icons.py)** - Batch generate inventory icons
- **[Environment Textures](examples/environment_textures.py)** - Create tileable background textures
- **[Real-time Godot Integration](examples/godot/)** - Live generation in Godot engine
- **[Procedural Sprite Variation](examples/sprite_variation.py)** - Generate sprite variations

### Running Examples

```bash
# Set configuration
export COMFYUI_URL="http://localhost:8188"

# Run character portrait example
python examples/character_portrait.py

# Run batch item icon generation
python examples/item_icons.py --count 10 --prompt "fantasy sword"
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/purlieu-studios/comfyui-mcp.git
cd comfyui-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=comfyui_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_client.py -v

# Run tests matching pattern
pytest tests/ -v -k "test_workflow"
```

### Code Quality Checks

```bash
# Type checking (strict mode)
mypy src/

# Linting
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Run all quality checks
pre-commit run --all-files
```

### Project Structure

```
comfyui-mcp/
├── src/
│   └── comfyui_mcp/           # Main package
│       ├── __init__.py        # Public API exports
│       ├── server.py          # MCP server implementation
│       ├── comfyui_client.py  # ComfyUI API client
│       ├── models.py          # Pydantic data models
│       ├── config.py          # Configuration management
│       ├── exceptions.py      # Custom exceptions
│       └── utils.py           # Utility functions
├── tests/                     # Test suite
│   ├── test_client.py         # Client tests
│   ├── test_models.py         # Model validation tests
│   ├── test_config.py         # Configuration tests
│   └── fixtures/              # Test fixtures
├── examples/                  # Example scripts
│   ├── character_portrait.py
│   ├── item_icons.py
│   └── godot/                 # Godot integration
├── workflows/                 # Workflow templates
│   ├── character-portrait.json
│   ├── item-icon.json
│   └── environment-texture.json
├── docs/                      # Documentation
│   ├── API.md
│   ├── CONFIGURATION.md
│   └── COMFYUI_API.md
├── .github/workflows/         # CI/CD
│   └── ci.yml
├── pyproject.toml             # Package configuration
├── README.md                  # This file
├── CLAUDE.md                  # AI assistant context
└── LICENSE                    # MIT License
```

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick contribution checklist:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest tests/`)
5. Run type checking (`mypy src/`)
6. Run linting (`ruff check src/ tests/`)
7. Format code (`ruff format src/ tests/`)
8. Commit changes (`git commit -m 'feat: add amazing feature'`)
9. Push to branch (`git push origin feature/amazing-feature`)
10. Open a Pull Request

---

## Troubleshooting

### Common Issues

#### ComfyUI Server Connection Failed

**Problem:** `ConnectionError: Cannot connect to ComfyUI server at http://localhost:8188`

**Solutions:**
1. Verify ComfyUI is running: Open `http://localhost:8188` in browser
2. Check URL configuration: Ensure `COMFYUI_URL` is correct
3. Check firewall settings: Allow connections on port 8188
4. Try explicit localhost: Use `http://127.0.0.1:8188` instead of `http://localhost:8188`

```python
# Test connection
from comfyui_mcp import ComfyUIClient, ComfyUIConfig

async def test_connection():
    config = ComfyUIConfig(url="http://127.0.0.1:8188")
    async with ComfyUIClient(config) as client:
        is_healthy = await client.health_check()
        print(f"Connection: {'✓' if is_healthy else '✗'}")
```

#### Workflow Execution Timeout

**Problem:** `TimeoutError: Workflow execution exceeded timeout of 120.0 seconds`

**Solutions:**
1. Increase timeout in configuration:
   ```toml
   [comfyui]
   timeout = 300.0  # 5 minutes
   ```

2. Reduce workflow complexity (fewer steps, lower resolution)
3. Check ComfyUI server logs for errors
4. Ensure models are downloaded and accessible

#### Module Import Errors

**Problem:** `ModuleNotFoundError: No module named 'comfyui_mcp'`

**Solutions:**
1. Reinstall package: `pip install -e .`
2. Activate virtual environment: `source venv/bin/activate`
3. Check Python path: `echo $PYTHONPATH`

#### Type Checking Errors

**Problem:** `mypy` reports type errors

**Solutions:**
1. Update type stubs: `pip install --upgrade types-all`
2. Check mypy configuration in `pyproject.toml`
3. Use `# type: ignore` for false positives (sparingly)

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now all ComfyUI MCP operations will log debug information
```

### Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/purlieu-studios/comfyui-mcp/issues)
- **GitHub Discussions**: [Ask questions and share ideas](https://github.com/purlieu-studios/comfyui-mcp/discussions)
- **Documentation**: [Read the docs](docs/)

---

## Roadmap

See [GitHub Milestones](https://github.com/purlieu-studios/comfyui-mcp/milestones) for upcoming features.

### Planned Features

- **Phase 1: Foundation** (Current)
  - ✅ ComfyUI API client
  - ✅ MCP server implementation
  - ✅ Basic workflow templates
  - ✅ Configuration system
  - ✅ Comprehensive documentation

- **Phase 2: Advanced Features** (Next)
  - [ ] WebSocket support for real-time progress
  - [ ] Advanced workflow template system
  - [ ] Image post-processing pipeline
  - [ ] Generation caching
  - [ ] Batch processing optimization

- **Phase 3: Godot Integration** (Future)
  - [ ] Godot GDScript helper library
  - [ ] Godot plugin for ComfyUI integration
  - [ ] Editor tools for workflow testing
  - [ ] Asset pipeline integration

- **Phase 4: Production Enhancements** (Future)
  - [ ] Authentication and API key support
  - [ ] Rate limiting and queue management
  - [ ] Monitoring and metrics
  - [ ] Docker containerization
  - [ ] Kubernetes deployment support

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** - Powerful workflow-based Stable Diffusion UI by comfyanonymous
- **[Godot Engine](https://godotengine.org/)** - Open-source game engine
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Universal AI integration standard by Anthropic
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation using Python type hints
- **[Ruff](https://github.com/astral-sh/ruff)** - Fast Python linter and formatter

---

## Support

- **Issues**: [GitHub Issues](https://github.com/purlieu-studios/comfyui-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/purlieu-studios/comfyui-mcp/discussions)
- **Documentation**: [docs/](docs/)

---

**Status**: Alpha - Active Development

Built with ❤️ by [Purlieu Studios](https://purlieu.studio)
