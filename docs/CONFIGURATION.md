# ComfyUI MCP Configuration

Complete guide to configuring the ComfyUI MCP Server using TOML configuration files or environment variables.

## Table of Contents

- [Overview](#overview)
- [Configuration Methods](#configuration-methods)
- [TOML Configuration File](#toml-configuration-file)
- [Environment Variables](#environment-variables)
- [Configuration Options](#configuration-options)
- [Example Configurations](#example-configurations)
- [Configuration Priority](#configuration-priority)
- [Validation Rules](#validation-rules)
- [Best Practices](#best-practices)

---

## Overview

The ComfyUI MCP Server can be configured using three methods:

1. **TOML Configuration File** (Recommended for projects)
2. **Environment Variables** (Recommended for deployment)
3. **Python Code** (Programmatic configuration)

All configuration methods use the same underlying `ComfyUIConfig` Pydantic model, ensuring consistent validation and behavior.

---

## Configuration Methods

### Method 1: TOML Configuration File

Create a `comfyui.toml` file in your project root:

```toml
[comfyui]
url = "http://localhost:8188"
api_key = "your-api-key-here"
timeout = 120.0
output_dir = "/path/to/output"
```

**Advantages:**
- Version-controlled configuration
- Easy to share across team
- Supports comments and documentation
- Type-safe with validation

**Use Cases:**
- Local development
- Team projects
- CI/CD environments

---

### Method 2: Environment Variables

Set environment variables in your shell or `.env` file:

```bash
export COMFYUI_URL="http://localhost:8188"
export COMFYUI_API_KEY="your-api-key-here"
export COMFYUI_TIMEOUT="120.0"
export COMFYUI_OUTPUT_DIR="/path/to/output"
```

**Advantages:**
- No files to manage
- Secure (not in version control)
- Standard deployment practice
- Works with Docker/containers

**Use Cases:**
- Production deployments
- Docker containers
- Cloud platforms (Heroku, AWS, etc.)
- CI/CD secrets management

---

### Method 3: Python Code

Configure programmatically in your Python code:

```python
from comfyui_mcp import ComfyUIConfig, ComfyUIClient

# Direct instantiation
config = ComfyUIConfig(
    url="http://localhost:8188",
    api_key="your-api-key-here",
    timeout=120.0,
    output_dir="/path/to/output"
)

# Use the config
async with ComfyUIClient(config) as client:
    # Your code here
    pass
```

**Advantages:**
- Maximum flexibility
- Dynamic configuration
- Conditional logic
- Runtime customization

**Use Cases:**
- Testing and development
- Dynamic server selection
- Custom configuration logic
- Programmatic control

---

## TOML Configuration File

### File Locations

The ComfyUI MCP Server searches for configuration files in the following order:

1. `./comfyui.toml` (Current directory)
2. `~/.config/comfyui/comfyui.toml` (User config directory)
3. `/etc/comfyui/comfyui.toml` (System-wide config)

### Basic Structure

```toml
# ComfyUI MCP Server Configuration
# https://github.com/PurlieuStudios/comfyui-mcp

[comfyui]
# ComfyUI server URL (required)
url = "http://localhost:8188"

# API key for authentication (optional)
# Minimum 8 characters if provided
api_key = "your-api-key-here"

# Request timeout in seconds (optional, default: 120.0)
# Range: 1.0 - 3600.0 seconds
timeout = 120.0

# Output directory for generated images (optional)
# Can be absolute or relative path
output_dir = "/path/to/output"
```

### Schema Specification

```toml
[comfyui]
# Required Fields
url = "string"  # Must start with http:// or https://

# Optional Fields
api_key = "string"      # Min 8 characters, or null
timeout = 120.0         # Float, range: 1.0 - 3600.0
output_dir = "string"   # Non-empty string, or null
```

---

## Environment Variables

### Supported Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `COMFYUI_URL` | String | **Yes** | None | ComfyUI server URL |
| `COMFYUI_API_KEY` | String | No | None | API key (min 8 chars) |
| `COMFYUI_TIMEOUT` | Float | No | 120.0 | Timeout in seconds |
| `COMFYUI_OUTPUT_DIR` | String | No | None | Output directory path |

### Loading from Environment

```python
from comfyui_mcp import ComfyUIConfig

# Load configuration from environment variables
config = ComfyUIConfig.from_env()
```

### Using with .env Files

Create a `.env` file (add to `.gitignore`!):

```bash
# .env
COMFYUI_URL=http://localhost:8188
COMFYUI_API_KEY=sk-your-secret-key-12345678
COMFYUI_TIMEOUT=60.0
COMFYUI_OUTPUT_DIR=./generated_images
```

Load with `python-dotenv`:

```python
from dotenv import load_dotenv
from comfyui_mcp import ComfyUIConfig

# Load .env file
load_dotenv()

# Load config from environment (now includes .env values)
config = ComfyUIConfig.from_env()
```

---

## Configuration Options

### `url` (Required)

ComfyUI server URL.

**Type:** `string`
**Format:** Must start with `http://` or `https://`
**Validation:** Trailing slashes are automatically removed

**Examples:**
```toml
# Local development
url = "http://localhost:8188"
url = "http://127.0.0.1:8188"

# Remote server
url = "https://comfyui.example.com"
url = "https://comfyui.example.com:8443"

# With path (advanced)
url = "http://localhost:8188/api/v1"
```

**Invalid:**
```toml
url = "localhost:8188"           # Missing protocol
url = "ftp://example.com"        # Wrong protocol
url = "http://localhost:8188///" # Trailing slashes (auto-fixed)
```

---

### `api_key` (Optional)

API key for ComfyUI server authentication.

**Type:** `string | null`
**Validation:** Minimum 8 characters if provided
**Default:** `null` (no authentication)

**Examples:**
```toml
# With API key
api_key = "sk-my-secret-key-12345678"
api_key = "prod-api-key-very-long-and-secure"

# No API key (local development)
# api_key = null  # or omit entirely
```

**Security Note:**
- Never commit API keys to version control
- Use environment variables for production
- Rotate keys regularly

---

### `timeout` (Optional)

Request timeout for ComfyUI API calls.

**Type:** `float`
**Range:** 1.0 - 3600.0 seconds (1 second to 1 hour)
**Default:** 120.0 seconds (2 minutes)

**Examples:**
```toml
# Fast workflows (simple generations)
timeout = 30.0

# Standard workflows
timeout = 120.0

# Complex workflows (high resolution, many steps)
timeout = 300.0

# Very long workflows
timeout = 600.0

# Maximum allowed
timeout = 3600.0  # 1 hour
```

**Guidelines:**
- **Simple text-to-image (512x512, 20 steps):** 30-60 seconds
- **Standard generation (1024x1024, 30 steps):** 60-120 seconds
- **High quality (1536x1536, 50 steps):** 180-300 seconds
- **Upscaling workflows:** 300-600 seconds
- **Video generation:** 600-3600 seconds

---

### `output_dir` (Optional)

Directory path for saving generated images.

**Type:** `string | null`
**Validation:** Non-empty, non-whitespace string
**Default:** `null` (use ComfyUI's default output directory)

**Examples:**
```toml
# Absolute paths
output_dir = "/var/comfyui/output"
output_dir = "C:\\Users\\user\\comfyui_output"  # Windows

# Relative paths
output_dir = "./generated_images"
output_dir = "../output"

# User home directory
output_dir = "~/comfyui_output"
```

**Path Handling:**
- Paths can be absolute or relative
- Windows backslashes must be escaped (`\\`) or use forward slashes
- Tilde (`~`) expands to user home directory
- Directory will be created if it doesn't exist (when loading files)

---

## Example Configurations

### Minimal Configuration

```toml
# comfyui.toml
[comfyui]
url = "http://localhost:8188"
```

### Development Configuration

```toml
# comfyui.toml
# Development environment configuration

[comfyui]
url = "http://localhost:8188"
timeout = 60.0  # Faster timeout for local testing
output_dir = "./dev_output"
```

### Production Configuration

```toml
# comfyui.toml
# Production environment configuration

[comfyui]
url = "https://comfyui.production.example.com"
timeout = 300.0  # Longer timeout for production workloads
output_dir = "/var/app/generated_images"

# API key should be set via environment variable:
# COMFYUI_API_KEY=your-production-api-key
```

### Multi-Environment Configuration

```toml
# comfyui.dev.toml
[comfyui]
url = "http://localhost:8188"
timeout = 30.0
output_dir = "./dev_output"
```

```toml
# comfyui.staging.toml
[comfyui]
url = "https://staging.comfyui.example.com"
timeout = 120.0
output_dir = "/mnt/staging/output"
```

```toml
# comfyui.prod.toml
[comfyui]
url = "https://comfyui.example.com"
timeout = 300.0
output_dir = "/mnt/production/output"
```

### High-Performance Configuration

```toml
# comfyui.toml
# Optimized for high-throughput processing

[comfyui]
url = "http://localhost:8188"
timeout = 600.0  # Long timeout for complex workflows
output_dir = "/mnt/ssd/comfyui_output"  # Fast SSD storage
```

### Docker Configuration

```toml
# comfyui.toml (mounted as volume)
[comfyui]
url = "http://comfyui-server:8188"  # Docker service name
timeout = 300.0
output_dir = "/app/output"  # Docker volume mount
```

With `docker-compose.yml`:

```yaml
version: '3.8'
services:
  comfyui-mcp:
    build: .
    volumes:
      - ./comfyui.toml:/app/comfyui.toml:ro
      - ./output:/app/output
    environment:
      - COMFYUI_API_KEY=${COMFYUI_API_KEY}
```

---

## Configuration Priority

When multiple configuration methods are used, the priority order is:

1. **Python code** (highest priority)
2. **Environment variables**
3. **TOML configuration file**
4. **Default values** (lowest priority)

### Example:

```toml
# comfyui.toml
[comfyui]
url = "http://localhost:8188"
timeout = 60.0
```

```bash
# Environment
export COMFYUI_TIMEOUT="300.0"
```

```python
# Python code
config = ComfyUIConfig(
    url="http://different:8188",  # Overrides TOML
    # timeout from environment (300.0)
)
```

**Result:**
- `url = "http://different:8188"` (from Python code)
- `timeout = 300.0` (from environment variable)
- Other fields use defaults

---

## Validation Rules

All configuration values are validated using Pydantic models.

### URL Validation

- **Must** start with `http://` or `https://`
- Trailing slashes are automatically removed
- Can include port numbers
- Can include path components

### API Key Validation

- **If provided**, must be at least 8 characters
- Can be omitted (defaults to `null`)
- Whitespace-only strings are rejected

### Timeout Validation

- **Must** be a float between 1.0 and 3600.0
- Values outside this range are rejected
- Strings are converted to floats

### Output Directory Validation

- **If provided**, must be non-empty and non-whitespace
- Can be omitted (defaults to `null`)
- Path existence is not validated (created on use)

### Example Validation Errors

```toml
# Invalid: URL missing protocol
url = "localhost:8188"  # ValidationError

# Invalid: API key too short
api_key = "short"  # ValidationError (< 8 chars)

# Invalid: Timeout out of range
timeout = 0.5  # ValidationError (< 1.0)
timeout = 5000.0  # ValidationError (> 3600.0)

# Invalid: Empty output directory
output_dir = ""  # ValidationError
output_dir = "   "  # ValidationError
```

---

## Best Practices

### 1. Use TOML for Project Configuration

Store project-specific settings in version-controlled `comfyui.toml`:

```toml
[comfyui]
url = "http://localhost:8188"
timeout = 120.0
output_dir = "./generated_images"
```

### 2. Use Environment Variables for Secrets

Keep sensitive data out of version control:

```bash
# .env (add to .gitignore)
COMFYUI_API_KEY=sk-production-key-12345678
```

### 3. Document Configuration in README

```markdown
## Configuration

Copy `comfyui.example.toml` to `comfyui.toml` and edit:

```toml
[comfyui]
url = "http://localhost:8188"
```

Set API key via environment variable:
```bash
export COMFYUI_API_KEY=your-key-here
```
```

### 4. Provide Example Configuration

Include `comfyui.example.toml` in repository:

```toml
# comfyui.example.toml
# Copy this file to comfyui.toml and customize

[comfyui]
url = "http://localhost:8188"
# api_key = "your-api-key-here"  # Uncomment and set
timeout = 120.0
# output_dir = "./generated_images"  # Uncomment to set
```

### 5. Use Different Configs Per Environment

```bash
# Development
export COMFYUI_CONFIG=comfyui.dev.toml

# Staging
export COMFYUI_CONFIG=comfyui.staging.toml

# Production
export COMFYUI_CONFIG=comfyui.prod.toml
```

### 6. Validate Configuration at Startup

```python
async def main():
    try:
        config = ComfyUIConfig.from_env()
        print(f"Loaded config: {config.url}")
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    async with ComfyUIClient(config) as client:
        # Check server availability
        if not await client.health_check():
            print("ComfyUI server not available")
            sys.exit(1)

        # Proceed with application
        ...
```

### 7. Use Type Hints for Config Values

```python
from comfyui_mcp import ComfyUIConfig

def get_config() -> ComfyUIConfig:
    """Load and validate configuration."""
    return ComfyUIConfig.from_env()
```

### 8. Handle Missing Configuration Gracefully

```python
import sys
from comfyui_mcp import ComfyUIConfig
from comfyui_mcp.exceptions import ComfyUIError

try:
    config = ComfyUIConfig.from_env()
except ValueError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    print("\nRequired environment variables:", file=sys.stderr)
    print("  COMFYUI_URL - ComfyUI server URL", file=sys.stderr)
    sys.exit(1)
```

---

## See Also

- [API Reference](./API.md) - Complete Python API documentation
- [ComfyUI API Integration](./COMFYUI_API.md) - REST API integration patterns
- [Environment Variables](./API.md#comfyuiconfig) - `ComfyUIConfig.from_env()` documentation
- [Examples](../examples/) - Configuration examples for various use cases

---

**Version:** 0.1.0
**License:** MIT
**Repository:** https://github.com/PurlieuStudios/comfyui-mcp
