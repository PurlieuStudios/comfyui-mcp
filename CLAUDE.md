# ComfyUI MCP Server

## Project Overview

This project implements a Model Context Protocol (MCP) server that integrates ComfyUI with a Godot game. The server acts as a bridge, allowing the Godot game to leverage ComfyUI's powerful workflow-based AI image generation capabilities.

## Purpose

The main goal is to enable real-time or on-demand AI image generation within a Godot game by:
- Exposing ComfyUI workflows as MCP tools
- Managing ComfyUI workflow execution
- Handling image generation requests from the game
- Providing workflow templates for common game assets (characters, items, environments, etc.)

## Architecture

### Components

1. **MCP Server** (Python)
   - Implements the Model Context Protocol specification
   - Exposes tools for interacting with ComfyUI
   - Manages workflow execution and result retrieval

2. **ComfyUI Integration**
   - Communicates with ComfyUI's API
   - Submits workflow prompts
   - Monitors generation progress
   - Retrieves generated images

3. **Godot Game Integration**
   - Game connects to MCP server via Claude Code or direct MCP client
   - Requests image generation based on game events
   - Receives generated assets for use in-game

### Expected Tools

- `generate_image`: Generate images using ComfyUI workflows
- `list_workflows`: List available workflow templates
- `get_workflow_status`: Check the status of a running workflow
- `cancel_workflow`: Cancel a running workflow
- `load_workflow`: Load a custom workflow from file

## Configuration

The server will be configured in `.mcp.json`:

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

## Project Structure

```
comfyui-mcp/
├── comfyui_mcp/
│   ├── __init__.py
│   ├── server.py          # Main MCP server implementation
│   ├── comfyui_client.py  # ComfyUI API client
│   ├── workflows/         # Workflow templates
│   └── utils.py           # Utility functions
├── tests/
│   └── test_server.py
├── .mcp.json              # MCP server configuration
├── requirements.txt       # Python dependencies
├── README.md              # User-facing documentation
└── CLAUDE.md              # This file (developer/AI context)
```

## Dependencies

- Python 3.8+
- `mcp` package for MCP protocol implementation
- `aiohttp` or `requests` for ComfyUI API communication
- `websockets` for real-time workflow monitoring
- `Pillow` for image handling (optional)

## Development Notes

### ComfyUI API Endpoints

The ComfyUI API typically runs on `http://127.0.0.1:8188` and provides:
- `/prompt` - Submit workflow prompts (POST)
- `/history` - Get workflow execution history (GET)
- `/queue` - View and manage the execution queue (GET)
- `/view` - Retrieve generated images (GET)

### Workflow Management

ComfyUI workflows are JSON-based node graphs. The server should:
1. Store common workflow templates
2. Allow parameter substitution (prompts, seeds, dimensions, etc.)
3. Track workflow execution state
4. Handle errors and retries

### Use Cases for Godot Game

- **Character Generation**: Generate NPC portraits or character sprites
- **Item Icons**: Create unique item icons based on descriptions
- **Environment Art**: Generate background textures or environmental elements
- **Dynamic Content**: Create procedural game assets on-the-fly
- **Concept Art**: Generate concept art for level design or storytelling

## Getting Started

1. Ensure ComfyUI is running locally
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.mcp.json` with correct ComfyUI URL
4. Run the server: `python -m comfyui_mcp.server`
5. Connect from Godot game or test via Claude Code

## Security Considerations

- Validate all workflow inputs to prevent injection attacks
- Rate-limit requests to prevent server overload
- Sanitize file paths when retrieving generated images
- Consider authentication for production deployments

## Future Enhancements

- Workflow caching for common requests
- Batch processing support
- Integration with Stable Diffusion model management
- Real-time generation progress updates via streaming
- Support for video generation workflows
- Integration with ControlNet for precise control
