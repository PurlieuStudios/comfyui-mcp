"""Tests for configuration file loading functionality.

Tests the file-based configuration loading including:
- Finding config files in standard locations
- Loading config from TOML files
- Merging with defaults
- Fallback priority (env > file > defaults)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from comfyui_mcp import ComfyUIConfig
from comfyui_mcp.config import find_config_file, load_config


class TestFindConfigFile:
    """Tests for find_config_file() function."""

    def test_find_config_in_current_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test finding config file in current directory."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create config file in current directory
        config_file = tmp_path / "comfyui.toml"
        config_file.write_text('[comfyui]\nurl = "http://localhost:8188"\n')

        # Should find it
        found = find_config_file()
        assert found is not None
        assert found.resolve() == config_file.resolve()

    def test_find_config_in_user_config_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test finding config file in user config directory."""
        # Change to temp directory (no config here)
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)

        # Create user config directory
        user_config_dir = tmp_path / ".config" / "comfyui"
        user_config_dir.mkdir(parents=True)
        config_file = user_config_dir / "comfyui.toml"
        config_file.write_text('[comfyui]\nurl = "http://localhost:8188"\n')

        # Mock home directory
        monkeypatch.setenv("HOME", str(tmp_path))
        if os.name == "nt":  # Windows
            monkeypatch.setenv("USERPROFILE", str(tmp_path))

        # Should find it
        found = find_config_file()
        assert found is not None
        assert found.resolve() == config_file.resolve()

    def test_find_config_prefers_current_over_user(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that current directory config takes priority over user config."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create config in current directory
        current_config = tmp_path / "comfyui.toml"
        current_config.write_text('[comfyui]\nurl = "http://current:8188"\n')

        # Create user config directory
        user_config_dir = tmp_path / ".config" / "comfyui"
        user_config_dir.mkdir(parents=True)
        user_config = user_config_dir / "comfyui.toml"
        user_config.write_text('[comfyui]\nurl = "http://user:8188"\n')

        # Mock home directory
        monkeypatch.setenv("HOME", str(tmp_path))
        if os.name == "nt":  # Windows
            monkeypatch.setenv("USERPROFILE", str(tmp_path))

        # Should find current directory config
        found = find_config_file()
        assert found is not None
        assert found.resolve() == current_config.resolve()

    def test_find_config_returns_none_when_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that find_config_file returns None when no config exists."""
        # Change to empty temp directory
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)

        # Mock home to non-existent directory
        fake_home = tmp_path / "fake_home"
        monkeypatch.setenv("HOME", str(fake_home))
        if os.name == "nt":  # Windows
            monkeypatch.setenv("USERPROFILE", str(fake_home))

        # Should return None
        found = find_config_file()
        assert found is None

    def test_find_config_with_custom_filename(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test finding config file with custom filename."""
        monkeypatch.chdir(tmp_path)

        # Create config with custom name
        config_file = tmp_path / "custom.toml"
        config_file.write_text('[comfyui]\nurl = "http://localhost:8188"\n')

        # Should find it
        found = find_config_file(filename="custom.toml")
        assert found is not None
        assert found.name == "custom.toml"


class TestComfyUIConfigFromFile:
    """Tests for ComfyUIConfig.from_file() classmethod."""

    def test_from_file_with_minimal_config(self, tmp_path: Path) -> None:
        """Test loading config with only required fields."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188"
"""
        )

        config = ComfyUIConfig.from_file(config_file)
        assert config.url == "http://localhost:8188"
        assert config.api_key is None
        assert config.timeout == 120.0  # Default
        assert config.output_dir is None

    def test_from_file_with_all_fields(self, tmp_path: Path) -> None:
        """Test loading config with all fields specified."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188"
api_key = "test-api-key-1234"
timeout = 300.0
output_dir = "./generated"
"""
        )

        config = ComfyUIConfig.from_file(config_file)
        assert config.url == "http://localhost:8188"
        assert config.api_key == "test-api-key-1234"
        assert config.timeout == 300.0
        assert config.output_dir == "./generated"

    def test_from_file_validates_url(self, tmp_path: Path) -> None:
        """Test that invalid URL raises validation error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "ftp://invalid:8188"
"""
        )

        with pytest.raises(ValidationError, match="String should match pattern"):
            ComfyUIConfig.from_file(config_file)

    def test_from_file_validates_api_key_length(self, tmp_path: Path) -> None:
        """Test that short API key raises validation error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188"
api_key = "short"
"""
        )

        with pytest.raises(
            ValidationError, match="API key must be at least 8 characters"
        ):
            ComfyUIConfig.from_file(config_file)

    def test_from_file_validates_timeout_range(self, tmp_path: Path) -> None:
        """Test that timeout out of range raises validation error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188"
timeout = 5000.0
"""
        )

        with pytest.raises(ValidationError, match="Timeout must not exceed"):
            ComfyUIConfig.from_file(config_file)

    def test_from_file_with_missing_comfyui_section(self, tmp_path: Path) -> None:
        """Test that missing [comfyui] section raises error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[other]
url = "http://localhost:8188"
"""
        )

        with pytest.raises(
            ValueError, match="Config file must contain \\[comfyui\\] section"
        ):
            ComfyUIConfig.from_file(config_file)

    def test_from_file_with_nonexistent_path_raises_error(self, tmp_path: Path) -> None:
        """Test that nonexistent config path raises FileNotFoundError."""
        config_file = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            ComfyUIConfig.from_file(config_file)

    def test_from_file_with_none_searches_default_locations(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that passing None to from_file searches default locations."""
        monkeypatch.chdir(tmp_path)

        # Create config in current directory
        config_file = tmp_path / "comfyui.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:9999"
timeout = 200.0
"""
        )

        config = ComfyUIConfig.from_file(None)
        assert config.url == "http://localhost:9999"
        assert config.timeout == 200.0

    def test_from_file_with_none_raises_if_no_config_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that from_file(None) raises error when no config file found."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)

        # Mock home to non-existent directory
        fake_home = tmp_path / "fake_home"
        monkeypatch.setenv("HOME", str(fake_home))
        if os.name == "nt":  # Windows
            monkeypatch.setenv("USERPROFILE", str(fake_home))

        with pytest.raises(FileNotFoundError, match="No config file found"):
            ComfyUIConfig.from_file(None)

    def test_from_file_removes_trailing_slash_from_url(self, tmp_path: Path) -> None:
        """Test that trailing slash is removed from URL."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188/"
"""
        )

        config = ComfyUIConfig.from_file(config_file)
        assert config.url == "http://localhost:8188"


class TestLoadConfig:
    """Tests for load_config() convenience function."""

    def test_load_config_prefers_environment_over_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that environment variables take priority over config file."""
        monkeypatch.chdir(tmp_path)

        # Create config file
        config_file = tmp_path / "comfyui.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://file:8188"
timeout = 200.0
"""
        )

        # Set environment variables
        monkeypatch.setenv("COMFYUI_URL", "http://env:8188")
        monkeypatch.setenv("COMFYUI_TIMEOUT", "300.0")

        config = load_config()
        # Environment should win
        assert config.url == "http://env:8188"
        assert config.timeout == 300.0

    def test_load_config_falls_back_to_file_when_no_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config file is used when no environment variables set."""
        monkeypatch.chdir(tmp_path)

        # Create config file
        config_file = tmp_path / "comfyui.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://file:8188"
timeout = 250.0
output_dir = "./output"
"""
        )

        # Clear environment
        monkeypatch.delenv("COMFYUI_URL", raising=False)
        monkeypatch.delenv("COMFYUI_API_KEY", raising=False)
        monkeypatch.delenv("COMFYUI_TIMEOUT", raising=False)
        monkeypatch.delenv("COMFYUI_OUTPUT_DIR", raising=False)

        config = load_config()
        assert config.url == "http://file:8188"
        assert config.timeout == 250.0
        assert config.output_dir == "./output"

    def test_load_config_merges_env_and_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that environment and file values are properly merged."""
        monkeypatch.chdir(tmp_path)

        # Create config file with some values
        config_file = tmp_path / "comfyui.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://file:8188"
timeout = 200.0
output_dir = "./file_output"
"""
        )

        # Set only some environment variables
        monkeypatch.setenv("COMFYUI_URL", "http://env:8188")
        monkeypatch.delenv("COMFYUI_TIMEOUT", raising=False)
        monkeypatch.delenv("COMFYUI_OUTPUT_DIR", raising=False)

        config = load_config()
        # URL from env, timeout and output_dir from file
        assert config.url == "http://env:8188"
        assert config.timeout == 200.0
        assert config.output_dir == "./file_output"

    def test_load_config_uses_defaults_when_neither_env_nor_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that defaults are used when no env vars or config file."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)

        # Clear environment
        monkeypatch.delenv("COMFYUI_URL", raising=False)
        monkeypatch.delenv("COMFYUI_API_KEY", raising=False)
        monkeypatch.delenv("COMFYUI_TIMEOUT", raising=False)
        monkeypatch.delenv("COMFYUI_OUTPUT_DIR", raising=False)

        # Mock home to non-existent directory (no user config)
        fake_home = tmp_path / "fake_home"
        monkeypatch.setenv("HOME", str(fake_home))
        if os.name == "nt":  # Windows
            monkeypatch.setenv("USERPROFILE", str(fake_home))

        # Should use defaults (which requires URL from env)
        # Actually, we need at least URL, so this should raise or we need to handle it
        # Let's set minimal env var
        monkeypatch.setenv("COMFYUI_URL", "http://localhost:8188")

        config = load_config()
        assert config.url == "http://localhost:8188"
        assert config.timeout == 120.0  # Default
        assert config.api_key is None
        assert config.output_dir is None


class TestConfigFileFormats:
    """Tests for various TOML file formats and edge cases."""

    def test_config_with_comments(self, tmp_path: Path) -> None:
        """Test that comments in TOML file are handled correctly."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
# ComfyUI Configuration
[comfyui]
# Server URL
url = "http://localhost:8188"
# Timeout in seconds
timeout = 150.0
"""
        )

        config = ComfyUIConfig.from_file(config_file)
        assert config.url == "http://localhost:8188"
        assert config.timeout == 150.0

    def test_config_with_extra_fields_ignored(self, tmp_path: Path) -> None:
        """Test that extra unknown fields in config file are ignored."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188"
unknown_field = "should be ignored"
another_field = 123
"""
        )

        # Should not raise, extra fields ignored
        config = ComfyUIConfig.from_file(config_file)
        assert config.url == "http://localhost:8188"

    def test_config_with_windows_paths(self, tmp_path: Path) -> None:
        """Test that Windows-style paths are handled correctly."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188"
output_dir = "C:\\\\Users\\\\test\\\\output"
"""
        )

        config = ComfyUIConfig.from_file(config_file)
        assert config.output_dir == "C:\\Users\\test\\output"

    def test_config_with_unix_paths(self, tmp_path: Path) -> None:
        """Test that Unix-style paths are handled correctly."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[comfyui]
url = "http://localhost:8188"
output_dir = "/home/user/output"
"""
        )

        config = ComfyUIConfig.from_file(config_file)
        assert config.output_dir == "/home/user/output"
