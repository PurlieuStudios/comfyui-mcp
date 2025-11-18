"""Tests for environment variable loading in ComfyUIConfig.

This module tests the ability to load ComfyUIConfig from environment variables,
supporting COMFYUI_URL, COMFYUI_API_KEY, COMFYUI_TIMEOUT, and COMFYUI_OUTPUT_DIR.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from comfyui_mcp.models import ComfyUIConfig


class TestConfigFromEnv:
    """Test loading ComfyUIConfig from environment variables."""

    def test_from_env_with_url_only(self) -> None:
        """Test loading config with only COMFYUI_URL set."""
        env = {"COMFYUI_URL": "http://localhost:8188"}

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        assert config.url == "http://localhost:8188"
        assert config.api_key is None
        assert config.timeout == 120.0  # Default
        assert config.output_dir is None

    def test_from_env_with_all_vars(self) -> None:
        """Test loading config with all environment variables set."""
        env = {
            "COMFYUI_URL": "https://comfyui.example.com:8443",
            "COMFYUI_API_KEY": "sk-test-api-key-12345",
            "COMFYUI_TIMEOUT": "60.0",
            "COMFYUI_OUTPUT_DIR": "/var/comfyui/output",
        }

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        assert config.url == "https://comfyui.example.com:8443"
        assert config.api_key == "sk-test-api-key-12345"
        assert config.timeout == 60.0
        assert config.output_dir == "/var/comfyui/output"

    def test_from_env_url_normalization(self) -> None:
        """Test that URL normalization works with environment variables."""
        env = {"COMFYUI_URL": "http://localhost:8188///"}

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        assert config.url == "http://localhost:8188"

    def test_from_env_missing_url_raises_error(self) -> None:
        """Test that missing COMFYUI_URL raises an error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                ComfyUIConfig.from_env()

        assert "COMFYUI_URL" in str(exc_info.value)

    def test_from_env_empty_url_raises_error(self) -> None:
        """Test that empty COMFYUI_URL raises an error."""
        env = {"COMFYUI_URL": ""}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises((ValueError, ValidationError)):
                ComfyUIConfig.from_env()

    def test_from_env_invalid_url_raises_error(self) -> None:
        """Test that invalid URL raises validation error."""
        env = {"COMFYUI_URL": "not-a-valid-url"}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                ComfyUIConfig.from_env()

    def test_from_env_api_key_validation(self) -> None:
        """Test that API key validation applies to environment variables."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "COMFYUI_API_KEY": "short",  # Less than 8 characters
        }

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                ComfyUIConfig.from_env()

        assert "api_key" in str(exc_info.value).lower()

    def test_from_env_timeout_type_conversion(self) -> None:
        """Test that timeout is converted from string to float."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "COMFYUI_TIMEOUT": "45.5",
        }

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        assert config.timeout == 45.5
        assert isinstance(config.timeout, float)

    def test_from_env_timeout_validation(self) -> None:
        """Test that timeout validation applies to environment variables."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "COMFYUI_TIMEOUT": "0.5",  # Less than 1.0 minimum
        }

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                ComfyUIConfig.from_env()

        assert "timeout" in str(exc_info.value).lower()

    def test_from_env_invalid_timeout_format(self) -> None:
        """Test that invalid timeout format raises an error."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "COMFYUI_TIMEOUT": "not-a-number",
        }

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises((ValueError, ValidationError)):
                ComfyUIConfig.from_env()

    def test_from_env_output_dir_validation(self) -> None:
        """Test that output directory validation applies to environment variables."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "COMFYUI_OUTPUT_DIR": "",  # Empty string
        }

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                ComfyUIConfig.from_env()

        assert "output_dir" in str(exc_info.value).lower()

    def test_from_env_with_extra_env_vars_ignored(self) -> None:
        """Test that extra environment variables are ignored."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "UNRELATED_VAR": "should-be-ignored",
            "PATH": "/usr/bin",
        }

        with patch.dict(os.environ, env, clear=False):
            config = ComfyUIConfig.from_env()

        assert config.url == "http://localhost:8188"

    def test_from_env_whitespace_trimmed(self) -> None:
        """Test that whitespace in environment variables is trimmed."""
        env = {
            "COMFYUI_URL": "  http://localhost:8188  ",
            "COMFYUI_API_KEY": "  api-key-12345678  ",
        }

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        assert config.url == "http://localhost:8188"
        assert config.api_key == "api-key-12345678"

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows environment variables are case-insensitive",
    )
    def test_from_env_case_sensitive(self) -> None:
        """Test that environment variable names are case-sensitive."""
        env = {"comfyui_url": "http://localhost:8188"}  # Lowercase

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError) as exc_info:
                ComfyUIConfig.from_env()

        assert "COMFYUI_URL" in str(exc_info.value)

    def test_from_env_with_windows_path(self) -> None:
        """Test loading config with Windows-style output directory path."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "COMFYUI_OUTPUT_DIR": "C:\\Users\\user\\output",
        }

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        assert config.output_dir == "C:\\Users\\user\\output"

    def test_from_env_multiple_calls_independent(self) -> None:
        """Test that multiple from_env() calls with different env vars work."""
        env1 = {"COMFYUI_URL": "http://server1:8188"}
        env2 = {"COMFYUI_URL": "http://server2:8188"}

        with patch.dict(os.environ, env1, clear=True):
            config1 = ComfyUIConfig.from_env()

        with patch.dict(os.environ, env2, clear=True):
            config2 = ComfyUIConfig.from_env()

        assert config1.url == "http://server1:8188"
        assert config2.url == "http://server2:8188"


class TestConfigEnvIntegration:
    """Test integration between environment loading and regular initialization."""

    def test_from_env_equivalent_to_direct_init(self) -> None:
        """Test that from_env() produces equivalent config to direct init."""
        env = {
            "COMFYUI_URL": "http://localhost:8188",
            "COMFYUI_API_KEY": "api-key-12345678",
            "COMFYUI_TIMEOUT": "90.0",
            "COMFYUI_OUTPUT_DIR": "/output",
        }

        with patch.dict(os.environ, env, clear=True):
            env_config = ComfyUIConfig.from_env()

        direct_config = ComfyUIConfig(
            url="http://localhost:8188",
            api_key="api-key-12345678",
            timeout=90.0,
            output_dir="/output",
        )

        assert env_config.url == direct_config.url
        assert env_config.api_key == direct_config.api_key
        assert env_config.timeout == direct_config.timeout
        assert env_config.output_dir == direct_config.output_dir

    def test_from_env_config_immutable(self) -> None:
        """Test that config loaded from env is immutable (frozen)."""
        env = {"COMFYUI_URL": "http://localhost:8188"}

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        with pytest.raises((ValueError, AttributeError, ValidationError)):
            config.url = "http://different:8188"

    def test_from_env_applies_all_validators(self) -> None:
        """Test that all field validators apply to env-loaded config."""
        env = {
            "COMFYUI_URL": "http://localhost:8188/",  # Trailing slash
            "COMFYUI_TIMEOUT": "3600.0",  # Maximum
        }

        with patch.dict(os.environ, env, clear=True):
            config = ComfyUIConfig.from_env()

        # URL validator should remove trailing slash
        assert config.url == "http://localhost:8188"
        # Timeout validator should allow maximum value
        assert config.timeout == 3600.0
