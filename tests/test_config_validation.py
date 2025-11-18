"""Tests for comprehensive configuration validation.

This module tests enhanced validation for ComfyUIConfig beyond basic
field type validation, including URL normalization, API key security,
timeout bounds, and output directory validation.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from comfyui_mcp.models import ComfyUIConfig


class TestURLValidation:
    """Test URL validation and normalization."""

    def test_url_trailing_slash_removed(self) -> None:
        """Test that trailing slashes are removed from URL."""
        config = ComfyUIConfig(url="http://127.0.0.1:8188/")

        assert config.url == "http://127.0.0.1:8188"
        assert not config.url.endswith("/")

    def test_url_multiple_trailing_slashes_removed(self) -> None:
        """Test that multiple trailing slashes are removed."""
        config = ComfyUIConfig(url="http://localhost:8188///")

        assert config.url == "http://localhost:8188"

    def test_url_preserves_path(self) -> None:
        """Test that URL path is preserved (only trailing slashes removed)."""
        config = ComfyUIConfig(url="http://example.com/api/v1")

        assert config.url == "http://example.com/api/v1"

    def test_url_preserves_path_removes_trailing_slash(self) -> None:
        """Test that path is preserved but trailing slash is removed."""
        config = ComfyUIConfig(url="http://example.com/api/v1/")

        assert config.url == "http://example.com/api/v1"

    def test_url_ftp_protocol_invalid(self) -> None:
        """Test that FTP protocol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="ftp://example.com")

        assert "url" in str(exc_info.value).lower()

    def test_url_no_protocol_invalid(self) -> None:
        """Test that URL without protocol is rejected."""
        with pytest.raises(ValidationError):
            ComfyUIConfig(url="localhost:8188")

    def test_url_with_port(self) -> None:
        """Test that URL with port is valid."""
        config = ComfyUIConfig(url="http://localhost:8080")

        assert config.url == "http://localhost:8080"

    def test_url_https_valid(self) -> None:
        """Test that HTTPS URLs are valid."""
        config = ComfyUIConfig(url="https://secure.example.com:443")

        assert config.url == "https://secure.example.com:443"

    def test_url_empty_string_invalid(self) -> None:
        """Test that empty URL string is rejected."""
        with pytest.raises(ValidationError):
            ComfyUIConfig(url="")

    def test_url_whitespace_only_invalid(self) -> None:
        """Test that whitespace-only URL is rejected."""
        with pytest.raises(ValidationError):
            ComfyUIConfig(url="   ")


class TestAPIKeyValidation:
    """Test API key validation."""

    def test_api_key_none_valid(self) -> None:
        """Test that None API key is valid (optional field)."""
        config = ComfyUIConfig(url="http://localhost:8188", api_key=None)

        assert config.api_key is None

    def test_api_key_valid_string(self) -> None:
        """Test that valid API key string is accepted."""
        config = ComfyUIConfig(
            url="http://localhost:8188",
            api_key="sk-1234567890abcdef",
        )

        assert config.api_key == "sk-1234567890abcdef"

    def test_api_key_empty_string_invalid(self) -> None:
        """Test that empty API key string is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="http://localhost:8188", api_key="")

        assert "api_key" in str(exc_info.value).lower()

    def test_api_key_whitespace_only_invalid(self) -> None:
        """Test that whitespace-only API key is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="http://localhost:8188", api_key="   ")

        assert "api_key" in str(exc_info.value).lower()

    def test_api_key_too_short_invalid(self) -> None:
        """Test that API key shorter than 8 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="http://localhost:8188", api_key="short")

        assert "api_key" in str(exc_info.value).lower()
        assert "8" in str(exc_info.value)  # Mentions minimum length

    def test_api_key_minimum_length_valid(self) -> None:
        """Test that API key with exactly 8 characters is valid."""
        config = ComfyUIConfig(url="http://localhost:8188", api_key="12345678")

        assert config.api_key == "12345678"

    def test_api_key_long_valid(self) -> None:
        """Test that long API keys are valid."""
        long_key = "sk-" + "a" * 100
        config = ComfyUIConfig(url="http://localhost:8188", api_key=long_key)

        assert config.api_key == long_key


class TestTimeoutValidation:
    """Test timeout validation."""

    def test_timeout_default_valid(self) -> None:
        """Test that default timeout (120.0) is valid."""
        config = ComfyUIConfig(url="http://localhost:8188")

        assert config.timeout == 120.0

    def test_timeout_positive_valid(self) -> None:
        """Test that positive timeout is valid."""
        config = ComfyUIConfig(url="http://localhost:8188", timeout=30.0)

        assert config.timeout == 30.0

    def test_timeout_minimum_one_second_valid(self) -> None:
        """Test that timeout of exactly 1.0 second is valid."""
        config = ComfyUIConfig(url="http://localhost:8188", timeout=1.0)

        assert config.timeout == 1.0

    def test_timeout_below_minimum_invalid(self) -> None:
        """Test that timeout below 1.0 second is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="http://localhost:8188", timeout=0.5)

        assert "timeout" in str(exc_info.value).lower()

    def test_timeout_maximum_valid(self) -> None:
        """Test that timeout at maximum (3600s = 1 hour) is valid."""
        config = ComfyUIConfig(url="http://localhost:8188", timeout=3600.0)

        assert config.timeout == 3600.0

    def test_timeout_above_maximum_invalid(self) -> None:
        """Test that timeout above 3600 seconds is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="http://localhost:8188", timeout=7200.0)

        assert "timeout" in str(exc_info.value).lower()

    def test_timeout_very_large_invalid(self) -> None:
        """Test that excessively large timeout is rejected."""
        with pytest.raises(ValidationError):
            ComfyUIConfig(url="http://localhost:8188", timeout=999999.0)


class TestOutputDirectoryValidation:
    """Test output directory validation."""

    def test_output_dir_none_valid(self) -> None:
        """Test that None output_dir is valid (optional field)."""
        config = ComfyUIConfig(url="http://localhost:8188", output_dir=None)

        assert config.output_dir is None

    def test_output_dir_valid_path(self) -> None:
        """Test that valid output directory path is accepted."""
        config = ComfyUIConfig(
            url="http://localhost:8188",
            output_dir="/path/to/output",
        )

        assert config.output_dir == "/path/to/output"

    def test_output_dir_windows_path_valid(self) -> None:
        """Test that Windows-style path is valid."""
        config = ComfyUIConfig(
            url="http://localhost:8188",
            output_dir="C:\\Users\\user\\output",
        )

        assert config.output_dir == "C:\\Users\\user\\output"

    def test_output_dir_relative_path_valid(self) -> None:
        """Test that relative path is valid."""
        config = ComfyUIConfig(
            url="http://localhost:8188",
            output_dir="./output",
        )

        assert config.output_dir == "./output"

    def test_output_dir_empty_string_invalid(self) -> None:
        """Test that empty output directory string is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="http://localhost:8188", output_dir="")

        assert "output_dir" in str(exc_info.value).lower()

    def test_output_dir_whitespace_only_invalid(self) -> None:
        """Test that whitespace-only output directory is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(url="http://localhost:8188", output_dir="   ")

        assert "output_dir" in str(exc_info.value).lower()


class TestConfigValidationIntegration:
    """Test integration of all validation rules."""

    def test_full_valid_config(self) -> None:
        """Test that fully valid configuration passes all validators."""
        config = ComfyUIConfig(
            url="https://comfyui.example.com:8443/api",
            api_key="sk-1234567890abcdef",
            timeout=60.0,
            output_dir="/var/comfyui/output",
        )

        assert config.url == "https://comfyui.example.com:8443/api"
        assert config.api_key == "sk-1234567890abcdef"
        assert config.timeout == 60.0
        assert config.output_dir == "/var/comfyui/output"

    def test_minimal_valid_config(self) -> None:
        """Test that minimal configuration with only URL is valid."""
        config = ComfyUIConfig(url="http://localhost:8188")

        assert config.url == "http://localhost:8188"
        assert config.api_key is None
        assert config.timeout == 120.0
        assert config.output_dir is None

    def test_multiple_validation_errors(self) -> None:
        """Test that multiple validation errors are reported."""
        with pytest.raises(ValidationError) as exc_info:
            ComfyUIConfig(
                url="",  # Invalid: empty
                api_key="",  # Invalid: empty
                timeout=0.0,  # Invalid: zero
                output_dir="",  # Invalid: empty
            )

        error_str = str(exc_info.value).lower()
        # All four fields should have validation errors
        assert "url" in error_str
        assert (
            "api_key" in error_str or "timeout" in error_str
        )  # At least one more error

    def test_config_immutable_after_creation(self) -> None:
        """Test that config cannot be modified after creation."""
        config = ComfyUIConfig(url="http://localhost:8188")

        with pytest.raises((ValueError, AttributeError, ValidationError)):
            config.url = "http://different:8188"
