# ComfyUI MCP Server - Configuration Examples

This directory contains example `.mcp.json` configuration files for integrating the ComfyUI MCP Server with Claude Code or other MCP-compatible clients.

## Quick Start

1. Choose the configuration example that best matches your use case
2. Copy it to your project's `.mcp.json` file
3. Customize the paths and URLs for your environment
4. Restart your MCP client (e.g., Claude Code)

## Available Examples

### [basic.mcp.json](./basic.mcp.json) - Minimal Configuration

The simplest possible configuration for local development.

**Use Case:** Quick start, testing, learning

**Features:**
- Connects to local ComfyUI server on default port
- Minimal configuration, uses all defaults
- No custom paths or directories

**When to Use:**
- First time setup
- Local development
- ComfyUI running on `localhost:8188`

```json
{
  "mcpServers": {
    "comfyui-mcp": {
      "command": "python",
      "args": ["-m", "comfyui_mcp.server"],
      "env": {
        "COMFYUI_URL": "http://localhost:8188"
      }
    }
  }
}
```

---

### [development.mcp.json](./development.mcp.json) - Development Setup

Standard configuration for local development with custom output directory and timeout settings.

**Use Case:** Local game development, asset generation

**Features:**
- Custom output directory for generated images
- Extended timeout for complex workflows
- Working directory specification

**When to Use:**
- Developing a game project
- Need organized output directories
- Working with complex workflows

**Customization:**
- Change `cwd` to your project directory
- Adjust `COMFYUI_OUTPUT_DIR` to preferred location
- Modify `COMFYUI_TIMEOUT` based on workflow complexity

---

### [production.mcp.json](./production.mcp.json) - Production Deployment

Configuration for production environments with remote ComfyUI server and API authentication.

**Use Case:** Production deployment, cloud hosting, team collaboration

**Features:**
- Remote ComfyUI server URL
- API key authentication (if ComfyUI has auth enabled)
- Extended timeout for production workloads
- Absolute paths for reliability

**When to Use:**
- Deploying to production
- ComfyUI on separate server/container
- Multiple developers sharing ComfyUI instance

**Security Notes:**
- **Never commit API keys to version control**
- Use environment variables or secrets management
- Consider using a `.env` file for sensitive values

---

### [custom-templates.mcp.json](./custom-templates.mcp.json) - Custom Template Directory

Configuration with custom workflow template directory for game-specific workflows.

**Use Case:** Custom workflows, game-specific templates

**Features:**
- Custom template directory path
- Custom output directory
- Project-specific working directory

**When to Use:**
- Created custom ComfyUI workflows for your game
- Organizing workflows by category or game system
- Multiple template directories for different asset types

**Workflow Organization:**
```
my-game-project/
├── my-custom-workflows/
│   ├── character-templates/
│   ├── environment-templates/
│   └── item-templates/
└── my-generated-images/
    ├── characters/
    ├── environments/
    └── items/
```

---

### [multi-server.mcp.json](./multi-server.mcp.json) - Multiple ComfyUI Instances

Configuration running multiple MCP server instances for different asset types or workflows.

**Use Case:** Large projects, specialized workflows, distributed generation

**Features:**
- Multiple MCP server instances
- Different template directories per server
- Different ComfyUI instances (optional)
- Organized output directories by asset type

**When to Use:**
- Large game projects with many asset types
- Different ComfyUI instances for different tasks
- Organizing workflows by category
- Load balancing across multiple ComfyUI servers

**Example Usage in Claude Code:**
```
# Character generation uses character-specific templates
generate character portrait using comfyui-character-gen

# Environment generation uses environment templates
generate forest texture using comfyui-environment-gen

# Item generation uses item templates
generate sword icon using comfyui-item-gen
```

---

### [docker.mcp.json](./docker.mcp.json) - Docker/Container Setup

Configuration for Docker/Kubernetes environments where ComfyUI runs in a container.

**Use Case:** Containerized deployment, Docker Compose, Kubernetes

**Features:**
- Container service name for URL
- Container filesystem paths
- Extended timeout for container overhead

**When to Use:**
- ComfyUI running in Docker container
- Docker Compose setup with multiple services
- Kubernetes deployment

**Example Docker Compose:**
```yaml
services:
  comfyui:
    image: comfyui/comfyui:latest
    ports:
      - "8188:8188"
    container_name: comfyui-container

  your-app:
    build: .
    volumes:
      - ./generated_images:/app/generated_images
    depends_on:
      - comfyui
```

---

### [windows.mcp.json](./windows.mcp.json) - Windows Environment

Configuration optimized for Windows development environments with Windows-style paths.

**Use Case:** Windows development, Windows-specific paths

**Features:**
- Windows-style backslash paths
- `127.0.0.1` instead of `localhost` (more reliable on Windows)
- Windows user directory structure

**When to Use:**
- Developing on Windows
- Need Windows path compatibility
- Experiencing localhost resolution issues on Windows

**Windows Path Notes:**
- Use double backslashes (`\\`) in JSON strings
- Or use forward slashes (`/`) - Python handles both on Windows
- Avoid UNC paths if possible

---

## Configuration Options Reference

### Required Fields

#### `command`
The Python executable to run the MCP server.

**Options:**
- `"python"` - Use system Python
- `"python3"` - Explicit Python 3
- `"/path/to/venv/bin/python"` - Specific Python interpreter

#### `args`
Arguments passed to the Python command.

**Standard:**
```json
["" m", "comfyui_mcp.server"]
```

**With Options:**
```json
["-m", "comfyui_mcp.server", "--template-dir", "./workflows"]
```

**Available Arguments:**
- `--template-dir <path>` - Custom workflow template directory
- `--comfyui-url <url>` - Override ComfyUI URL (also set via env)
- `--config <path>` - Load from TOML config file

### Environment Variables

#### `COMFYUI_URL` (Required)
URL of the ComfyUI server API.

**Format:** `http://host:port` or `https://host:port`
**Default:** `http://localhost:8188`
**Examples:**
- `http://localhost:8188` - Local server
- `http://192.168.1.100:8188` - Network server
- `http://comfyui-container:8188` - Docker service
- `https://comfyui.example.com:8188` - Remote HTTPS

#### `COMFYUI_OUTPUT_DIR` (Optional)
Directory where generated images will be saved.

**Format:** Absolute or relative path
**Default:** Current directory
**Examples:**
- `./generated_images` - Relative to working directory
- `/var/comfyui/output` - Absolute path (Linux)
- `C:\\Users\\Name\\output` - Absolute path (Windows)

#### `COMFYUI_TIMEOUT` (Optional)
Timeout for workflow execution in seconds.

**Format:** Decimal number (1.0 - 3600.0)
**Default:** `120.0` (2 minutes)
**Examples:**
- `60.0` - 1 minute (simple workflows)
- `120.0` - 2 minutes (standard)
- `300.0` - 5 minutes (complex workflows)
- `600.0` - 10 minutes (very complex workflows)

#### `COMFYUI_API_KEY` (Optional)
API key for ComfyUI authentication (if enabled on server).

**Format:** String, minimum 8 characters
**Security:** Never commit API keys to version control
**Best Practice:** Use environment variables or secrets manager

### Optional Fields

#### `cwd` (Current Working Directory)
Sets the working directory for the MCP server process.

**Use Cases:**
- Resolve relative paths correctly
- Access project-specific resources
- Organize generated files by project

#### `env`
Environment variables passed to the MCP server process.

**Note:** All `COMFYUI_*` variables should go here.

---

## Common Scenarios

### Scenario 1: Game Development Studio

**Requirements:**
- Multiple developers
- Shared ComfyUI server
- Organized workflows by asset type
- Network-accessible ComfyUI

**Recommended Config:** `production.mcp.json` with team-specific modifications

```json
{
  "mcpServers": {
    "comfyui-mcp": {
      "command": "python",
      "args": ["-m", "comfyui_mcp.server"],
      "env": {
        "COMFYUI_URL": "http://comfyui-server.studio.local:8188",
        "COMFYUI_OUTPUT_DIR": "/mnt/shared/game-assets/generated",
        "COMFYUI_TIMEOUT": "180.0"
      }
    }
  }
}
```

### Scenario 2: Solo Indie Developer

**Requirements:**
- Local ComfyUI
- Simple setup
- Quick iterations

**Recommended Config:** `basic.mcp.json` or `development.mcp.json`

### Scenario 3: Cloud/Distributed Setup

**Requirements:**
- ComfyUI in cloud (AWS, GCP, Azure)
- API authentication
- High availability

**Recommended Config:** `production.mcp.json` with cloud URLs

```json
{
  "mcpServers": {
    "comfyui-mcp": {
      "command": "python",
      "args": ["-m", "comfyui_mcp.server"],
      "env": {
        "COMFYUI_URL": "https://comfyui-api.your-cloud.com",
        "COMFYUI_API_KEY": "${COMFYUI_API_KEY}",
        "COMFYUI_TIMEOUT": "300.0"
      }
    }
  }
}
```

### Scenario 4: Asset Pipeline Automation

**Requirements:**
- Different workflows for different asset types
- Batch processing
- Organized output

**Recommended Config:** `multi-server.mcp.json`

---

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to ComfyUI server

**Solutions:**
1. Verify ComfyUI is running: Open `http://localhost:8188` in browser
2. Check `COMFYUI_URL` matches your ComfyUI server address
3. Try `127.0.0.1` instead of `localhost`
4. Check firewall settings

### Path Issues

**Problem:** Templates not found or output directory errors

**Solutions:**
1. Use absolute paths for reliability
2. On Windows, use double backslashes (`\\`) or forward slashes (`/`)
3. Verify `cwd` is set correctly
4. Check directory exists and has write permissions

### Timeout Issues

**Problem:** Workflows timing out

**Solutions:**
1. Increase `COMFYUI_TIMEOUT` value
2. Simplify workflow (fewer steps, lower resolution)
3. Check ComfyUI server isn't overloaded
4. Verify models are downloaded and accessible

### Permission Issues

**Problem:** Cannot write to output directory

**Solutions:**
1. Check directory permissions (`chmod` on Linux/Mac)
2. Run with appropriate user privileges
3. Use directory within your home folder
4. Create directory first: `mkdir -p ./generated_images`

---

## Next Steps

1. **Choose a configuration** that matches your use case
2. **Copy to `.mcp.json`** in your project root
3. **Customize paths** for your environment
4. **Test the connection:**
   ```bash
   # Test ComfyUI connection
   python -m comfyui_mcp.cli test-connection
   ```
5. **List available workflows:**
   ```bash
   python -m comfyui_mcp.cli list-templates
   ```
6. **Generate your first image** via Claude Code or the CLI

---

## Additional Resources

- **[Main README](../../README.md)** - Project overview and quick start
- **[Configuration Guide](../../docs/CONFIGURATION.md)** - Comprehensive configuration documentation
- **[MCP Tools Documentation](../../docs/MCP_TOOLS.md)** - MCP tool usage and examples
- **[Workflow Templates](../../docs/WORKFLOW_TEMPLATES.md)** - Creating and using workflow templates

---

## Contributing

Found an issue with these examples or have a suggestion for a new configuration scenario? Please:

1. [Open an issue](https://github.com/purlieu-studios/comfyui-mcp/issues)
2. [Start a discussion](https://github.com/purlieu-studios/comfyui-mcp/discussions)
3. Submit a pull request with your improvements

---

Built with ❤️ for game developers using ComfyUI
