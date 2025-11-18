"""Command-line interface for ComfyUI MCP Server.

This module provides a Click-based CLI for interacting with ComfyUI through
the MCP server. It supports:
- Global configuration options (--config, --comfyui-url, --template-dir)
- Extensible command structure for subcommands
- Configuration file and environment variable integration
- User-friendly error messages and help text

Example:
    >>> # Show help
    >>> comfyui --help
    >>>
    >>> # Use custom configuration
    >>> comfyui --config myconfig.toml COMMAND
    >>>
    >>> # Override ComfyUI URL
    >>> comfyui --comfyui-url http://localhost:9999 COMMAND
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from comfyui_mcp import __version__
from comfyui_mcp.config import load_config
from comfyui_mcp.models import ComfyUIConfig


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to TOML configuration file",
)
@click.option(
    "--comfyui-url",
    type=str,
    help="ComfyUI server URL (overrides config file)",
)
@click.option(
    "--template-dir",
    type=click.Path(path_type=Path),
    help="Directory containing workflow templates",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@click.version_option(version=__version__, prog_name="comfyui-mcp")
@click.pass_context
def cli(
    ctx: click.Context,
    config: Path | None,
    comfyui_url: str | None,
    template_dir: Path | None,
    verbose: bool,
) -> None:
    """ComfyUI MCP Server - AI-powered image generation for Godot games.

    This CLI provides commands for interacting with ComfyUI through the
    Model Context Protocol (MCP) server. It enables workflow-based image
    generation, template management, and server operations.

    Configuration Priority (highest to lowest):
    1. Command-line arguments (--comfyui-url, --template-dir)
    2. Environment variables (COMFYUI_URL, COMFYUI_OUTPUT_DIR)
    3. Configuration file (--config or auto-discovered)
    4. Default values

    Examples:
        # Show available commands
        comfyui --help

        # Use custom configuration file
        comfyui --config myconfig.toml list-templates

        # Override ComfyUI server URL
        comfyui --comfyui-url http://localhost:9999 generate

    For more information, visit: https://github.com/purlieu-studios/comfyui-mcp
    """
    # Initialize context object to store shared state
    ctx.ensure_object(dict)

    # Store verbose flag
    ctx.obj["verbose"] = verbose

    # Load configuration with precedence:
    # 1. Try to load from file or auto-discover
    # 2. Override with command-line arguments
    # 3. Store in context for subcommands
    try:
        # Load base configuration (handles env vars and file discovery)
        comfyui_config = load_config()

        # Override with command-line arguments if provided
        if comfyui_url:
            # Create new config with overridden URL
            comfyui_config = ComfyUIConfig(
                url=comfyui_url,
                api_key=comfyui_config.api_key,
                timeout=comfyui_config.timeout,
                output_dir=comfyui_config.output_dir,
            )

        # Store in context
        ctx.obj["config"] = comfyui_config
        ctx.obj["template_dir"] = template_dir

        if verbose:
            click.echo(f"Loaded configuration: {comfyui_config.url}", err=True)

    except Exception as e:
        # Handle configuration errors gracefully
        if verbose:
            click.echo(f"Warning: Error loading configuration: {e}", err=True)
            click.echo("Using default configuration...", err=True)

        # Fall back to default config
        try:
            comfyui_config = ComfyUIConfig(url="http://localhost:8188")
            ctx.obj["config"] = comfyui_config
            ctx.obj["template_dir"] = template_dir
        except Exception as fallback_error:
            click.echo(
                f"Error: Could not initialize configuration: {fallback_error}",
                err=True,
            )
            sys.exit(1)


# Subcommands will be added here by future implementations (Issues #50-52)
# Example structure for future commands:
#
# @cli.command()
# @click.pass_context
# def generate(ctx: click.Context) -> None:
#     """Generate images using ComfyUI workflows."""
#     config = ctx.obj["config"]
#     # Implementation here
#
# @cli.command()
# @click.pass_context
# def list_templates(ctx: click.Context) -> None:
#     """List available workflow templates."""
#     config = ctx.obj["config"]
#     # Implementation here


def main() -> None:
    """Main entry point for the CLI application.

    This function is registered as a console script entry point in pyproject.toml.
    It invokes the Click CLI application with proper exception handling.
    """
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
