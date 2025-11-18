# Epic: ComfyUI MCP Server Foundation

**Priority**: High
**Estimated Duration**: 4 weeks
**Labels**: mcp, comfyui, foundation, infrastructure, ai-generation
**Milestone**: v0.1.0

## Description

Establish the foundational infrastructure for the ComfyUI MCP server, enabling AI-powered image generation for Godot game development. This epic creates a bridge between ComfyUI's workflow-based generation system and the Godot game engine through the Model Context Protocol, allowing dynamic generation of game assets (character sprites, item icons, environment textures, etc.) during development or runtime.

**Technology Stack:**
- Backend: Python 3.10+ with async/await
- MCP SDK: mcp>=1.0.0
- HTTP Client: aiohttp>=3.9.0
- WebSockets: websockets>=12.0
- Data Validation: Pydantic>=2.0.0
- Image Processing: Pillow>=10.0.0
- Testing: pytest>=7.4.0, pytest-asyncio>=0.21.0, pytest-aiohttp>=1.0.0

## Goals

- Complete Python project structure following epic-tasks pattern
- Working ComfyUI API client with workflow submission and monitoring
- Functional MCP server with core image generation tools
- Workflow template system for common game asset types
- Comprehensive test coverage and documentation
- Integration examples for Godot game development

## Tasks

### Project Setup & Infrastructure
- [ ] Initialize Python package structure (src/comfyui_mcp/, tests/, examples/, workflows/) `[infrastructure, setup]` `2sp`
- [ ] Create pyproject.toml with dependencies and build configuration `[infrastructure, setup]` `3sp` `depends-on: #1`
- [ ] Set up development tooling (ruff, mypy, pytest) `[infrastructure, dev-tools]` `2sp` `depends-on: #2`
- [ ] Configure pre-commit hooks for code quality `[infrastructure, dev-tools]` `1sp` `depends-on: #3`
- [ ] Create .gitignore and initial git configuration `[infrastructure, setup]` `1sp`
- [ ] Set up GitHub repository and CI/CD workflows `[infrastructure, ci]` `5sp` `depends-on: #4`

### Core Data Models
- [ ] Define Pydantic models for WorkflowPrompt (nodes, parameters, seed) `[backend, models]` `5sp`
- [ ] Create WorkflowTemplate model (name, description, parameters, nodes) `[backend, models]` `3sp` `depends-on: #7`
- [ ] Define GenerationRequest model (template_id, params, output_settings) `[backend, models]` `3sp` `depends-on: #7`
- [ ] Create GenerationResult model (images, metadata, execution_time) `[backend, models]` `2sp` `depends-on: #7`
- [ ] Define ComfyUIConfig model (url, api_key, timeout, output_dir) `[backend, models]` `2sp` `depends-on: #7`
- [ ] Create WorkflowStatus model (queue_position, progress, state) `[backend, models]` `2sp` `depends-on: #7`
- [ ] Add model validation and serialization tests `[testing, models]` `3sp` `depends-on: #7, #8, #9, #10, #11, #12`

### ComfyUI API Client Integration
- [ ] Implement ComfyUIClient base class with aiohttp session management `[backend, comfyui]` `5sp`
- [ ] Add ComfyUI server connection validation and health check `[backend, comfyui]` `2sp` `depends-on: #14`
- [ ] Create submit_workflow method for POST /prompt `[backend, comfyui]` `5sp` `depends-on: #14`
- [ ] Implement get_queue_status for workflow monitoring `[backend, comfyui]` `3sp` `depends-on: #14`
- [ ] Add get_history method for execution results `[backend, comfyui]` `3sp` `depends-on: #14`
- [ ] Implement download_image method for retrieving generated images `[backend, comfyui]` `5sp` `depends-on: #14`
- [ ] Create cancel_workflow method for queue management `[backend, comfyui]` `2sp` `depends-on: #14`
- [ ] Add WebSocket support for real-time progress updates `[backend, comfyui, websocket]` `8sp` `depends-on: #14`
- [ ] Implement retry logic with exponential backoff `[backend, comfyui, error-handling]` `3sp` `depends-on: #14`
- [ ] Add comprehensive error handling and logging `[backend, comfyui, error-handling]` `3sp` `depends-on: #14`
- [ ] Write unit tests for ComfyUIClient `[testing, comfyui]` `8sp` `depends-on: #14, #15, #16, #17, #18, #19, #20, #21, #22, #23`

### Workflow Template System
- [ ] Design workflow template file format (JSON schema) `[backend, templates, design]` `3sp`
- [ ] Implement WorkflowTemplateManager for loading/saving templates `[backend, templates]` `5sp` `depends-on: #25`
- [ ] Create parameter substitution engine for templates `[backend, templates]` `5sp` `depends-on: #26`
- [ ] Create character portrait workflow template (SD 1.5 base) `[templates, content]` `5sp` `depends-on: #26`
- [ ] Create item icon workflow template (512x512 centered) `[templates, content]` `3sp` `depends-on: #26`
- [ ] Create environment texture workflow template (tileable) `[templates, content]` `3sp` `depends-on: #26`
- [ ] Create pixel art workflow template (upscale + pixelate) `[templates, content]` `5sp` `depends-on: #26`
- [ ] Implement template validation logic `[backend, templates, validation]` `3sp` `depends-on: #26`
- [ ] Add template metadata and tagging system `[backend, templates]` `2sp` `depends-on: #26`
- [ ] Write tests for template system `[testing, templates]` `5sp` `depends-on: #26, #27, #28, #29, #30, #31, #32, #33`

### Image Generation Orchestration
- [ ] Create ImageGenerator class for workflow orchestration `[backend, generation]` `5sp`
- [ ] Implement generate_from_template with async workflow submission `[backend, generation]` `5sp` `depends-on: #35`
- [ ] Add batch generation support for multiple images `[backend, generation]` `5sp` `depends-on: #35`
- [ ] Implement generation queue management `[backend, generation]` `3sp` `depends-on: #35`
- [ ] Create progress tracking and callback system `[backend, generation]` `5sp` `depends-on: #35`
- [ ] Add image post-processing (resize, format conversion) `[backend, generation]` `3sp` `depends-on: #35`
- [ ] Implement caching for common generation requests `[backend, generation, optimization]` `5sp` `depends-on: #35`
- [ ] Write unit tests for ImageGenerator `[testing, generation]` `8sp` `depends-on: #35, #36, #37, #38, #39, #40, #41`

### MCP Server Implementation
- [ ] Create server.py with MCP server initialization `[mcp, server]` `3sp`
- [ ] Implement generate_image MCP tool with full parameters `[mcp, server]` `5sp` `depends-on: #43`
- [ ] Implement list_workflows MCP tool for template discovery `[mcp, server]` `2sp` `depends-on: #43`
- [ ] Implement get_workflow_status MCP tool `[mcp, server]` `3sp` `depends-on: #43`
- [ ] Implement cancel_workflow MCP tool `[mcp, server]` `2sp` `depends-on: #43`
- [ ] Implement load_workflow MCP tool for custom workflows `[mcp, server]` `3sp` `depends-on: #43`
- [ ] Add proper error handling and response formatting `[mcp, server, error-handling]` `3sp` `depends-on: #43`
- [ ] Create MCP server configuration examples for .mcp.json `[mcp, documentation]` `2sp` `depends-on: #43`
- [ ] Write integration tests for MCP tools `[testing, mcp]` `8sp` `depends-on: #44, #45, #46, #47, #48, #49`

### CLI Commands (Optional)
- [ ] Create cli.py with Click command group `[cli, interface]` `3sp`
- [ ] Implement 'generate' CLI command `[cli, interface]` `3sp` `depends-on: #52`
- [ ] Implement 'list-templates' CLI command `[cli, interface]` `2sp` `depends-on: #52`
- [ ] Implement 'test-connection' CLI command `[cli, interface]` `2sp` `depends-on: #52`
- [ ] Add rich terminal output with progress bars `[cli, interface, ui]` `3sp` `depends-on: #52`
- [ ] Create CLI usage examples and help text `[cli, documentation]` `2sp` `depends-on: #52`

### Configuration System
- [ ] Define configuration schema (TOML format) `[config, design]` `2sp`
- [ ] Implement config file loader with defaults `[config, backend]` `3sp` `depends-on: #58`
- [ ] Add environment variable support (COMFYUI_URL, COMFYUI_OUTPUT_DIR) `[config, backend]` `2sp` `depends-on: #59`
- [ ] Create configuration validation `[config, backend, validation]` `2sp` `depends-on: #59`
- [ ] Generate example configuration file `[config, documentation]` `1sp` `depends-on: #59`
- [ ] Write tests for configuration system `[testing, config]` `3sp` `depends-on: #59, #60, #61, #62`

### Documentation
- [ ] Write comprehensive README.md with quick start guide `[documentation]` `5sp`
- [ ] Create API documentation for all public methods `[documentation]` `5sp`
- [ ] Document ComfyUI API integration patterns `[documentation]` `3sp`
- [ ] Create MCP tool usage guide `[documentation, mcp]` `3sp`
- [ ] Document workflow template system and format `[documentation, templates]` `5sp`
- [ ] Create Godot integration guide `[documentation, godot]` `5sp`
- [ ] Write workflow creation tutorial `[documentation, tutorial]` `5sp`
- [ ] Create CONTRIBUTING.md for developers `[documentation]` `2sp`

### Testing & Quality Assurance
- [ ] Set up pytest configuration and fixtures `[testing, infrastructure]` `2sp`
- [ ] Create mock ComfyUI API server for testing `[testing, infrastructure]` `8sp` `depends-on: #72`
- [ ] Achieve 80%+ code coverage `[testing, quality]` `8sp` `depends-on: #73`
- [ ] Run mypy type checking with strict mode `[testing, quality]` `3sp`
- [ ] Run ruff linting and formatting checks `[testing, quality]` `1sp`
- [ ] Perform integration testing with real ComfyUI instance `[testing, integration]` `8sp` `depends-on: #73`
- [ ] Create test fixtures with sample workflows `[testing, infrastructure]` `3sp` `depends-on: #73`
- [ ] Test WebSocket connection handling `[testing, integration, websocket]` `5sp` `depends-on: #73`

### Example Projects
- [ ] Create example: character portrait generation for RPG `[examples, godot]` `3sp`
- [ ] Create example: item icon batch generation `[examples, godot]` `3sp`
- [ ] Create example: environment texture generation `[examples, godot]` `3sp`
- [ ] Create example: real-time generation in Godot `[examples, godot]` `5sp`
- [ ] Create example: procedural sprite variation `[examples, godot]` `3sp`

### Godot Integration Support
- [ ] Design Godot GDScript helper class for MCP communication `[godot, integration]` `5sp`
- [ ] Create Godot plugin structure for ComfyUI integration `[godot, integration]` `8sp` `depends-on: #79`
- [ ] Implement Godot texture loading from generated images `[godot, integration]` `3sp` `depends-on: #80`
- [ ] Add Godot editor tools for workflow testing `[godot, integration, tools]` `5sp` `depends-on: #80`
- [ ] Write Godot integration documentation `[godot, documentation]` `5sp` `depends-on: #80`

## Acceptance Criteria

- Python package installs successfully with `pip install -e .`
- ComfyUI API client connects to local ComfyUI instance
- MCP server starts and responds to tool requests
- Can generate images from workflow templates
- Can monitor generation progress in real-time
- Can cancel running workflows
- Generated images are saved to configured output directory
- All MCP tools work as documented
- Test coverage is 80% or higher
- All type hints pass mypy strict checking
- Code passes ruff linting without errors
- Documentation is complete with examples
- Godot integration examples work correctly

## Dependencies

- ComfyUI must be installed and running locally (http://127.0.0.1:8188)
- Stable Diffusion models downloaded and available in ComfyUI
- Python 3.10 or higher
- GitHub repository for issue tracking
- CI/CD environment (GitHub Actions)
- Godot 4.x for integration testing (optional)

## Risks

- **ComfyUI API changes**: ComfyUI API is not officially versioned
  - Mitigation: Version pinning, API compatibility layer, monitor ComfyUI releases
- **Workflow compatibility**: Different ComfyUI installations may have different nodes
  - Mitigation: Validate required nodes before execution, provide node installation guide
- **Long generation times**: AI image generation can be slow (30s-2min+)
  - Mitigation: Async operations, progress updates, timeout configuration
- **Memory usage**: ComfyUI can consume significant GPU/CPU memory
  - Mitigation: Queue management, batch size limits, resource monitoring
- **WebSocket stability**: Real-time updates may be unreliable
  - Mitigation: Fallback to polling, connection retry logic
- **Model availability**: Required SD models may not be installed
  - Mitigation: Check model availability, provide model installation guide

## Notes

- Focus on async operations for non-blocking generation
- Keep workflow templates simple and well-documented
- Provide clear error messages for common issues (ComfyUI not running, models missing)
- Consider rate limiting for production use
- Plan for custom node support in Phase 2
- Document ComfyUI setup requirements clearly
- Test with multiple SD model types (1.5, XL, custom)
- Consider adding A1111 API compatibility in future
- Godot integration should work with both Godot 3.x and 4.x
- Plan for workflow versioning and migration

---
