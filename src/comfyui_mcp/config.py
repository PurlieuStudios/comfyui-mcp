"""Configuration file loading utilities for ComfyUI MCP Server.

This module provides functions for loading configuration from TOML files
with support for standard file locations and fallback priority.

Configuration Priority (highest to lowest):
    1. Environment variables (COMFYUI_URL, COMFYUI_API_KEY, etc.)
    2. Configuration file (searched in standard locations)
    3. Default values

Standard Configuration File Locations (searched in order):
    1. ./comfyui.toml (current directory)
    2. ~/.config/comfyui/comfyui.toml (user config directory)
    3. /etc/comfyui/comfyui.toml (system-wide config, Unix only)

Example:
    >>> # Load config with automatic fallback
    >>> config = load_config()
    >>> print(config.url)
    http://localhost:8188

    >>> # Or find config file manually
    >>> config_path = find_config_file()
    >>> if config_path:
    ...     config = ComfyUIConfig.from_file(config_path)
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib

from comfyui_mcp.models import ComfyUIConfig


def find_config_file(filename: str = "comfyui.toml") -> Path | None:
    """Search for configuration file in standard locations.

    Searches for a configuration file in the following order:
    1. Current directory (./comfyui.toml)
    2. User config directory (~/.config/comfyui/comfyui.toml)
    3. System directory (/etc/comfyui/comfyui.toml, Unix only)

    Args:
        filename: Name of the configuration file to search for.
                  Defaults to "comfyui.toml".

    Returns:
        Path to the first configuration file found, or None if no
        configuration file exists in any of the standard locations.

    Example:
        >>> config_path = find_config_file()
        >>> if config_path:
        ...     print(f"Found config at: {config_path}")
        ... else:
        ...     print("No config file found")
    """
    # List of paths to search (in priority order)
    search_paths: list[Path] = []

    # 1. Current directory
    search_paths.append(Path.cwd() / filename)

    # 2. User config directory
    if os.name == "nt":  # Windows
        # Windows: %USERPROFILE%\.config\comfyui\comfyui.toml
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            search_paths.append(Path(user_profile) / ".config" / "comfyui" / filename)
    else:  # Unix-like (Linux, macOS)
        # Unix: ~/.config/comfyui/comfyui.toml
        home = os.environ.get("HOME")
        if home:
            search_paths.append(Path(home) / ".config" / "comfyui" / filename)

    # 3. System directory (Unix only)
    if os.name != "nt":
        search_paths.append(Path("/etc") / "comfyui" / filename)

    # Search for the first existing file
    for path in search_paths:
        if path.exists() and path.is_file():
            return path

    return None


def load_config() -> ComfyUIConfig:
    """Load configuration with automatic fallback priority.

    Loads configuration using the following priority (highest to lowest):
    1. Environment variables (COMFYUI_URL, COMFYUI_API_KEY, etc.)
    2. Configuration file (searches standard locations)
    3. Default values

    Environment variables always take precedence over file-based configuration.
    If an environment variable is not set, the corresponding value from the
    config file is used. If neither is set, the default value is used.

    Returns:
        ComfyUIConfig instance with values loaded from the highest priority
        source available for each configuration field.

    Raises:
        ValidationError: If configuration values fail validation (e.g., invalid URL,
                         timeout out of range, API key too short).

    Example:
        >>> # Load config with automatic fallback
        >>> config = load_config()
        >>> print(f"ComfyUI URL: {config.url}")
        >>> print(f"Timeout: {config.timeout}s")

    Note:
        This function will attempt to merge values from multiple sources:
        - URL from environment, timeout from file, defaults for others
        - All values from file if no environment variables set
        - All defaults if neither environment nor file available
    """
    # Start with values from config file if available
    config_data: dict[str, str | float | None] = {}

    # Try to load from config file
    config_file = find_config_file()
    if config_file is not None:
        try:
            with open(config_file, "rb") as f:
                toml_data = tomllib.load(f)

            if "comfyui" in toml_data:
                file_config = toml_data["comfyui"]
                # Extract values from file
                if "url" in file_config:
                    config_data["url"] = file_config["url"]
                if "api_key" in file_config:
                    config_data["api_key"] = file_config["api_key"]
                if "timeout" in file_config:
                    config_data["timeout"] = float(file_config["timeout"])
                if "output_dir" in file_config:
                    config_data["output_dir"] = file_config["output_dir"]
        except Exception:
            # If file loading fails, just continue without it
            pass

    # Override with environment variables (higher priority)
    env_url = os.environ.get("COMFYUI_URL")
    if env_url:
        config_data["url"] = env_url.strip()

    env_api_key = os.environ.get("COMFYUI_API_KEY")
    if env_api_key:
        config_data["api_key"] = env_api_key.strip()

    env_timeout = os.environ.get("COMFYUI_TIMEOUT")
    if env_timeout:
        try:
            config_data["timeout"] = float(env_timeout)
        except ValueError:
            pass  # Ignore invalid timeout, use default or file value

    env_output_dir = os.environ.get("COMFYUI_OUTPUT_DIR")
    if env_output_dir:
        config_data["output_dir"] = env_output_dir.strip()

    # If no URL from either source, must come from environment or will fail validation
    # The ComfyUIConfig constructor will handle validation
    return ComfyUIConfig(**config_data)  # type: ignore[arg-type]
