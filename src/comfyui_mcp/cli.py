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

import asyncio
import sys
from pathlib import Path
from typing import Any

import click

from comfyui_mcp import __version__
from comfyui_mcp.comfyui_client import ComfyUIClient
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


# Subcommands will be added here by future implementations (Issues #50-51)


@cli.command("test-connection")
@click.pass_context
def test_connection(ctx: click.Context) -> None:
    """Test connection to the ComfyUI server.

    This command attempts to connect to the configured ComfyUI server
    and reports whether the connection was successful. It performs a
    health check on the server's API endpoint.

    The command uses the configuration from:
    1. --comfyui-url command-line option (highest priority)
    2. COMFYUI_URL environment variable
    3. Configuration file
    4. Default (http://localhost:8188)

    Exit codes:
        0: Connection successful
        1: Connection failed

    Examples:
        # Test connection using default or configured URL
        comfyui test-connection

        # Test connection to a specific URL
        comfyui --comfyui-url http://192.168.1.100:8188 test-connection

        # Show verbose output
        comfyui --verbose test-connection
    """
    config: ComfyUIConfig = ctx.obj["config"]
    verbose: bool = ctx.obj.get("verbose", False)

    # Show which URL we're testing
    click.echo(f"Testing connection to ComfyUI server at: {config.url}")

    async def _test_connection() -> dict[str, Any]:
        """Inner async function to perform the health check."""
        async with ComfyUIClient(config) as client:
            return await client.health_check()

    # Run the async health check
    try:
        result = asyncio.run(_test_connection())

        # Check if connection was successful
        if result.get("connected", False):
            click.echo(click.style("✓ Connection successful!", fg="green"))

            # Show additional details in verbose mode
            if verbose:
                click.echo(f"  URL: {result.get('url', 'N/A')}")
                if "status_code" in result:
                    click.echo(f"  Status: {result['status_code']}")
                if "response_time" in result:
                    click.echo(f"  Response time: {result['response_time']:.3f}s")

            sys.exit(0)
        else:
            # Connection failed
            click.echo(click.style("✗ Connection failed", fg="red"), err=True)

            # Show error details
            error_msg = result.get("error", "Unknown error")
            click.echo(f"  Error: {error_msg}", err=True)

            if verbose and "url" in result:
                click.echo(f"  Attempted URL: {result['url']}", err=True)

            sys.exit(1)

    except Exception as e:
        # Handle unexpected errors
        click.echo(
            click.style(f"✗ Error testing connection: {e}", fg="red"),
            err=True,
        )
        if verbose:
            import traceback

            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


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
