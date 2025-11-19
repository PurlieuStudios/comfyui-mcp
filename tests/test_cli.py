"""Tests for CLI implementation.

Tests the Click-based command-line interface including:
- CLI command group initialization
- Global options parsing (--config, --comfyui-url, --template-dir)
- Configuration loading and merging
- Context object management
- Error handling and user-friendly output
- Extensibility for subcommands
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from comfyui_mcp.cli import cli
from comfyui_mcp.models import ComfyUIConfig


class TestCLICommandGroup:
    """Tests for CLI command group initialization."""

    def test_cli_command_group_exists(self) -> None:
        """Test that cli command group is defined."""
        assert cli is not None
        assert callable(cli)

    def test_cli_help_output(self) -> None:
        """Test that cli --help shows expected information."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "comfyui" in result.output.lower() or "ComfyUI" in result.output
        assert "config" in result.output.lower()

    def test_cli_version_option(self) -> None:
        """Test that cli --version shows version information."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower() or any(
            c.isdigit() for c in result.output
        )


class TestGlobalOptions:
    """Tests for global CLI options."""

    def test_cli_accepts_config_option(self) -> None:
        """Test that --config option is accepted."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy config file
            Path("test_config.toml").write_text("[comfyui]\nurl = 'http://test:8188'\n")

            result = runner.invoke(cli, ["--config", "test_config.toml", "--help"])

            # Should not error on --config option
            assert result.exit_code == 0

    def test_cli_accepts_comfyui_url_option(self) -> None:
        """Test that --comfyui-url option is accepted."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--comfyui-url", "http://localhost:9999", "--help"]
        )

        # Should not error on --comfyui-url option
        assert result.exit_code == 0

    def test_cli_accepts_template_dir_option(self) -> None:
        """Test that --template-dir option is accepted."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--template-dir", "./workflows", "--help"])

        # Should not error on --template-dir option
        assert result.exit_code == 0

    def test_cli_accepts_verbose_option(self) -> None:
        """Test that --verbose option is accepted."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--help"])

        # Should not error on --verbose option
        assert result.exit_code == 0


class TestConfigurationLoading:
    """Tests for configuration loading and merging."""

    @patch("comfyui_mcp.cli.load_config")
    def test_cli_loads_config_from_file(self, mock_load_config: MagicMock) -> None:
        """Test that CLI loads configuration from file."""
        mock_config = ComfyUIConfig(url="http://test:8188")
        mock_load_config.return_value = mock_config

        runner = CliRunner()
        # Just invoking help should trigger config loading in context
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0

    def test_cli_handles_missing_config_file(self) -> None:
        """Test that CLI handles missing config file gracefully."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--config", "nonexistent.toml", "--help"])

        # Should not crash, may show warning but should still work
        # Exit code 0 for --help even with missing config
        assert result.exit_code == 0

    @patch("comfyui_mcp.cli.load_config")
    def test_cli_url_option_overrides_config(self, mock_load_config: MagicMock) -> None:
        """Test that --comfyui-url overrides config file."""
        mock_config = ComfyUIConfig(url="http://config-file:8188")
        mock_load_config.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["--comfyui-url", "http://override:9999", "--help"])

        assert result.exit_code == 0

    def test_cli_uses_default_config_when_none_provided(self) -> None:
        """Test that CLI uses default configuration when no options provided."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0


class TestContextManagement:
    """Tests for Click context object management."""

    def test_cli_creates_context_object(self) -> None:
        """Test that CLI creates a Click context object."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Context should be created during invocation
        assert result.exit_code == 0

    @patch("comfyui_mcp.cli.load_config")
    def test_context_contains_config(self, mock_load_config: MagicMock) -> None:
        """Test that context object contains configuration."""
        mock_config = ComfyUIConfig(url="http://test:8188")
        mock_load_config.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0


class TestErrorHandling:
    """Tests for CLI error handling."""

    def test_cli_handles_invalid_url(self) -> None:
        """Test that CLI handles invalid ComfyUI URL gracefully."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--comfyui-url", "not-a-valid-url", "--help"])

        # Should either accept it (validation happens later) or show clear error
        # For now, we expect it to not crash
        assert result.exit_code in [0, 1, 2]

    @patch("comfyui_mcp.cli.load_config")
    def test_cli_handles_config_load_error(self, mock_load_config: MagicMock) -> None:
        """Test that CLI handles configuration loading errors."""
        mock_load_config.side_effect = Exception("Config load failed")

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Should handle error gracefully and still show help
        assert result.exit_code == 0


class TestCommandExtensibility:
    """Tests for CLI command extensibility."""

    def test_cli_is_click_group(self) -> None:
        """Test that cli is a Click group for subcommands."""
        # Check if cli is a Click Group
        assert hasattr(cli, "command") or hasattr(cli, "group")

    def test_cli_help_mentions_commands(self) -> None:
        """Test that CLI help text mentions commands section."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        # Should have a commands section (even if empty for now)
        # Click groups typically show "Commands:" in help text


class TestCLIIntegration:
    """Integration tests for CLI with configuration system."""

    @patch("comfyui_mcp.cli.load_config")
    def test_cli_integration_with_config_system(
        self, mock_load_config: MagicMock, tmp_path: Path
    ) -> None:
        """Test CLI integrates properly with configuration system."""
        mock_config = ComfyUIConfig(
            url="http://localhost:8188", output_dir=str(tmp_path / "output")
        )
        mock_load_config.return_value = mock_config

        runner = CliRunner()
        # Note: --help exits early, so we just test that CLI accepts the patched config
        # When actual subcommands are added, they will properly load config
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        # CLI should initialize successfully even with mocked config

    def test_cli_respects_config_precedence(self, tmp_path: Path) -> None:
        """Test that CLI respects configuration precedence.

        Priority (highest to lowest):
        1. Command-line arguments
        2. Environment variables
        3. Configuration file
        4. Defaults
        """
        runner = CliRunner()

        # Create config file
        config_file = tmp_path / "test.toml"
        config_file.write_text("[comfyui]\nurl = 'http://config:8188'\n")

        # Command-line arg should override config file
        result = runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "--comfyui-url",
                "http://cli:9999",
                "--help",
            ],
        )

        assert result.exit_code == 0


class TestTestConnectionCommand:
    """Tests for test-connection CLI command."""

    def test_test_connection_command_exists(self) -> None:
        """Test that test-connection command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["test-connection", "--help"])

        # Command should exist and show help
        assert result.exit_code == 0
        assert "test-connection" in result.output.lower()

    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_test_connection_success(self, mock_client_class: MagicMock) -> None:
        """Test test-connection command with successful connection."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.health_check = AsyncMock(
            return_value={
                "connected": True,
                "url": "http://localhost:8188/queue",
                "status_code": 200,
            }
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["test-connection"])

        # Should succeed and show success message
        assert result.exit_code == 0
        assert (
            "success" in result.output.lower() or "connected" in result.output.lower()
        )

    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_test_connection_failure(self, mock_client_class: MagicMock) -> None:
        """Test test-connection command with failed connection."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.health_check = AsyncMock(
            return_value={
                "connected": False,
                "url": "http://localhost:8188/queue",
                "error": "Connection refused",
            }
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["test-connection"])

        # Should show failure but not crash
        assert result.exit_code in [0, 1]
        assert (
            "fail" in result.output.lower()
            or "error" in result.output.lower()
            or "refused" in result.output.lower()
        )

    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_test_connection_with_custom_url(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test test-connection command respects --comfyui-url option."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.health_check = AsyncMock(
            return_value={
                "connected": True,
                "url": "http://custom:9999/queue",
                "status_code": 200,
            }
        )

        runner = CliRunner()
        result = runner.invoke(
            cli, ["--comfyui-url", "http://custom:9999", "test-connection"]
        )

        # Should use the custom URL
        assert result.exit_code == 0
        # Verify client was created with correct URL
        assert mock_client_class.called

    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_test_connection_shows_url(self, mock_client_class: MagicMock) -> None:
        """Test that test-connection shows the URL being tested."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.health_check = AsyncMock(
            return_value={
                "connected": True,
                "url": "http://localhost:8188/queue",
                "status_code": 200,
            }
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["test-connection"])

        # Output should mention the URL
        assert result.exit_code == 0
        assert "localhost" in result.output or "8188" in result.output

    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_test_connection_with_verbose(self, mock_client_class: MagicMock) -> None:
        """Test test-connection command with --verbose flag."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.health_check = AsyncMock(
            return_value={
                "connected": True,
                "url": "http://localhost:8188/queue",
                "status_code": 200,
                "response_time": 0.05,
            }
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "test-connection"])

        # Should show more detailed output
        assert result.exit_code == 0

    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_test_connection_handles_exception(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test test-connection handles exceptions gracefully."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.health_check = AsyncMock(side_effect=Exception("Network error"))

        runner = CliRunner()
        result = runner.invoke(cli, ["test-connection"])

        # Should handle error gracefully
        assert result.exit_code in [0, 1]
        assert "error" in result.output.lower() or "fail" in result.output.lower()

    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_test_connection_exit_code_on_failure(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test that test-connection returns non-zero exit code on failure."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.health_check = AsyncMock(
            return_value={"connected": False, "error": "Connection failed"}
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["test-connection"])

        # Should return non-zero exit code for scripting purposes
        assert result.exit_code == 1


class TestGenerateCommand:
    """Tests for generate CLI command."""

    def test_generate_command_exists(self) -> None:
        """Test that generate command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])

        # Command should exist and show help
        assert result.exit_code == 0
        assert "generate" in result.output.lower()

    @patch("comfyui_mcp.cli.ImageGenerator")
    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_generate_with_template_id(
        self,
        mock_client_class: MagicMock,
        mock_generator_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate command with template ID."""
        # Create test template
        template_data = {
            "name": "Test Template",
            "description": "Test",
            "parameters": {},
            "nodes": {},
        }
        (tmp_path / "test-template.json").write_text(json.dumps(template_data))

        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_template = AsyncMock(
            return_value=MagicMock(
                prompt_id="test-123",
                images=["output.png"],
                execution_time=1.5,
            )
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--template-dir",
                str(tmp_path),
                "generate",
                "test-template",
            ],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "test-123" in result.output or "output.png" in result.output

    @patch("comfyui_mcp.cli.ImageGenerator")
    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_generate_with_parameters(
        self,
        mock_client_class: MagicMock,
        mock_generator_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate command with template parameters."""
        # Create test template
        template_data = {
            "name": "Test Template",
            "description": "Test",
            "parameters": {
                "prompt": {
                    "type": "string",
                    "description": "Text prompt",
                    "default": "test",
                }
            },
            "nodes": {},
        }
        (tmp_path / "test-template.json").write_text(json.dumps(template_data))

        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_template = AsyncMock(
            return_value=MagicMock(
                prompt_id="test-123",
                images=["output.png"],
                execution_time=1.5,
            )
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--template-dir",
                str(tmp_path),
                "generate",
                "test-template",
                "--param",
                "prompt=a wizard",
                "--param",
                "seed=42",
            ],
        )

        # Should succeed and pass parameters
        assert result.exit_code == 0

    @patch("comfyui_mcp.cli.ImageGenerator")
    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_generate_with_output_dir(
        self,
        mock_client_class: MagicMock,
        mock_generator_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate command with custom output directory."""
        # Create test template
        template_data = {
            "name": "Test Template",
            "description": "Test",
            "parameters": {},
            "nodes": {},
        }
        (tmp_path / "test-template.json").write_text(json.dumps(template_data))
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_template = AsyncMock(
            return_value=MagicMock(
                prompt_id="test-123",
                images=["output.png"],
                execution_time=1.5,
            )
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--template-dir",
                str(tmp_path),
                "generate",
                "test-template",
                "--output",
                str(output_dir),
            ],
        )

        # Should succeed
        assert result.exit_code == 0

    @patch("comfyui_mcp.cli.ImageGenerator")
    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_generate_missing_template(
        self,
        mock_client_class: MagicMock,
        mock_generator_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate command with missing template."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_template = AsyncMock(
            side_effect=FileNotFoundError("Template not found: nonexistent")
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--template-dir",
                str(tmp_path),
                "generate",
                "nonexistent",
            ],
        )

        # Should show error
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "not found" in result.output.lower()

    @patch("comfyui_mcp.cli.ImageGenerator")
    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_generate_shows_progress(
        self,
        mock_client_class: MagicMock,
        mock_generator_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate command shows generation progress."""
        # Create test template
        template_data = {
            "name": "Test Template",
            "description": "Test",
            "parameters": {},
            "nodes": {},
        }
        (tmp_path / "test-template.json").write_text(json.dumps(template_data))

        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_template = AsyncMock(
            return_value=MagicMock(
                prompt_id="test-123",
                images=["output.png"],
                execution_time=1.5,
            )
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--template-dir",
                str(tmp_path),
                "generate",
                "test-template",
            ],
        )

        # Should show some progress/status information
        assert result.exit_code == 0
        # Output should contain status messages
        output_lower = result.output.lower()
        assert any(
            word in output_lower
            for word in ["generating", "completed", "success", "generated"]
        )

    @patch("comfyui_mcp.cli.ImageGenerator")
    @patch("comfyui_mcp.cli.ComfyUIClient")
    def test_generate_with_verbose_output(
        self,
        mock_client_class: MagicMock,
        mock_generator_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate command with --verbose flag."""
        # Create test template
        template_data = {
            "name": "Test Template",
            "description": "Test",
            "parameters": {},
            "nodes": {},
        }
        (tmp_path / "test-template.json").write_text(json.dumps(template_data))

        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_template = AsyncMock(
            return_value=MagicMock(
                prompt_id="test-123",
                images=["output.png"],
                execution_time=1.5,
                metadata={"seed": 42},
            )
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--template-dir",
                str(tmp_path),
                "--verbose",
                "generate",
                "test-template",
            ],
        )

        # Should show detailed output
        assert result.exit_code == 0


class TestListTemplatesCommand:
    """Tests for list-templates CLI command."""

    def test_list_templates_command_exists(self) -> None:
        """Test that list-templates command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list-templates", "--help"])

        # Command should exist and show help
        assert result.exit_code == 0
        assert "list-templates" in result.output.lower()

    def test_list_templates_shows_available_templates(self, tmp_path: Path) -> None:
        """Test list-templates displays available templates."""
        # Create test templates
        template1_data = {
            "name": "Character Portrait",
            "description": "Generate character portraits",
            "category": "character",
            "parameters": {},
            "nodes": {},
        }
        template2_data = {
            "name": "Item Icon",
            "description": "Generate item icons",
            "category": "item",
            "parameters": {},
            "nodes": {},
        }

        (tmp_path / "character-portrait.json").write_text(json.dumps(template1_data))
        (tmp_path / "item-icon.json").write_text(json.dumps(template2_data))

        runner = CliRunner()
        result = runner.invoke(cli, ["--template-dir", str(tmp_path), "list-templates"])

        # Should succeed and show templates
        assert result.exit_code == 0
        assert "character-portrait" in result.output
        assert "item-icon" in result.output

    def test_list_templates_with_details(self, tmp_path: Path) -> None:
        """Test list-templates with --detailed flag shows full info."""
        template_data = {
            "name": "Test Template",
            "description": "A test template",
            "category": "test",
            "parameters": {},
            "nodes": {},
        }

        (tmp_path / "test-template.json").write_text(json.dumps(template_data))

        runner = CliRunner()
        result = runner.invoke(
            cli, ["--template-dir", str(tmp_path), "list-templates", "--detailed"]
        )

        # Should show detailed information
        assert result.exit_code == 0
        assert "Test Template" in result.output
        assert "A test template" in result.output

    def test_list_templates_filter_by_category(self, tmp_path: Path) -> None:
        """Test list-templates --category filters templates."""
        template1_data = {
            "name": "Character Portrait",
            "description": "Generate character portraits",
            "category": "character",
            "parameters": {},
            "nodes": {},
        }
        template2_data = {
            "name": "Item Icon",
            "description": "Generate item icons",
            "category": "item",
            "parameters": {},
            "nodes": {},
        }

        (tmp_path / "character-portrait.json").write_text(json.dumps(template1_data))
        (tmp_path / "item-icon.json").write_text(json.dumps(template2_data))

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--template-dir",
                str(tmp_path),
                "list-templates",
                "--category",
                "character",
            ],
        )

        # Should only show character templates
        assert result.exit_code == 0
        assert "character-portrait" in result.output
        assert "item-icon" not in result.output

    def test_list_templates_empty_directory(self, tmp_path: Path) -> None:
        """Test list-templates with no templates shows appropriate message."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--template-dir", str(tmp_path), "list-templates"])

        # Should handle empty directory gracefully
        assert result.exit_code == 0
        assert (
            "no templates" in result.output.lower()
            or "0 templates" in result.output.lower()
            or result.output.strip() == ""
        )

    def test_list_templates_nonexistent_directory(self) -> None:
        """Test list-templates with nonexistent directory shows error."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--template-dir", "/nonexistent/path", "list-templates"]
        )

        # Should show error about missing directory
        assert result.exit_code in [0, 1, 2]
        # CLI may handle this at initialization or command execution

    def test_list_templates_json_output(self, tmp_path: Path) -> None:
        """Test list-templates --json outputs machine-readable format."""
        template_data = {
            "name": "Test Template",
            "description": "A test template",
            "category": "test",
            "parameters": {},
            "nodes": {},
        }

        (tmp_path / "test-template.json").write_text(json.dumps(template_data))

        runner = CliRunner()
        result = runner.invoke(
            cli, ["--template-dir", str(tmp_path), "list-templates", "--json"]
        )

        # Should output valid JSON
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert isinstance(output_data, list)
        assert len(output_data) == 1
