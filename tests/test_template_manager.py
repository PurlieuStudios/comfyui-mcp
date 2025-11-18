"""Tests for WorkflowTemplateManager.

Tests the template management system including:
- Loading templates from a directory
- Caching and retrieving templates
- Listing available templates
- Filtering by category
- Error handling for missing/invalid templates
"""

from __future__ import annotations

from pathlib import Path

import pytest

from comfyui_mcp import TemplateParameter, WorkflowNode, WorkflowTemplate
from comfyui_mcp.template_manager import WorkflowTemplateManager


class TestWorkflowTemplateManagerInitialization:
    """Tests for WorkflowTemplateManager initialization."""

    def test_create_manager_with_path_object(self, tmp_path: Path) -> None:
        """Test creating manager with Path object."""
        manager = WorkflowTemplateManager(tmp_path)
        assert manager.template_dir == tmp_path

    def test_create_manager_with_string_path(self, tmp_path: Path) -> None:
        """Test creating manager with string path."""
        manager = WorkflowTemplateManager(str(tmp_path))
        assert manager.template_dir == tmp_path

    def test_create_manager_with_nonexistent_directory_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Test that creating manager with non-existent directory raises error."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError, match="Template directory not found"):
            WorkflowTemplateManager(nonexistent)

    def test_create_manager_with_file_instead_of_directory_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Test that creating manager with file path raises error."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("not a directory")

        with pytest.raises(ValueError, match="Template directory must be a directory"):
            WorkflowTemplateManager(file_path)


class TestWorkflowTemplateManagerListTemplates:
    """Tests for listing available templates."""

    def test_list_templates_empty_directory(self, tmp_path: Path) -> None:
        """Test listing templates in empty directory."""
        manager = WorkflowTemplateManager(tmp_path)
        templates = manager.list_templates()
        assert templates == []

    def test_list_templates_with_json_files(self, tmp_path: Path) -> None:
        """Test listing templates when JSON files exist."""
        # Create template files
        template1 = WorkflowTemplate(
            name="Template 1", description="First template", parameters={}, nodes={}
        )
        template1.to_file(tmp_path / "template1.json")

        template2 = WorkflowTemplate(
            name="Template 2", description="Second template", parameters={}, nodes={}
        )
        template2.to_file(tmp_path / "template2.json")

        manager = WorkflowTemplateManager(tmp_path)
        templates = manager.list_templates()

        assert len(templates) == 2
        assert "template1" in templates
        assert "template2" in templates

    def test_list_templates_ignores_non_json_files(self, tmp_path: Path) -> None:
        """Test that non-JSON files are ignored."""
        # Create template file
        template = WorkflowTemplate(
            name="Valid Template",
            description="A valid template",
            parameters={},
            nodes={},
        )
        template.to_file(tmp_path / "valid.json")

        # Create non-JSON files
        (tmp_path / "README.md").write_text("# Templates")
        (tmp_path / "config.txt").write_text("config")
        (tmp_path / ".gitignore").write_text("*.pyc")

        manager = WorkflowTemplateManager(tmp_path)
        templates = manager.list_templates()

        assert len(templates) == 1
        assert templates == ["valid"]

    def test_list_templates_sorted_alphabetically(self, tmp_path: Path) -> None:
        """Test that templates are listed in alphabetical order."""
        # Create templates with names that would be unsorted
        for name in ["zebra", "apple", "mountain", "banana"]:
            template = WorkflowTemplate(
                name=name.title(),
                description=f"{name} template",
                parameters={},
                nodes={},
            )
            template.to_file(tmp_path / f"{name}.json")

        manager = WorkflowTemplateManager(tmp_path)
        templates = manager.list_templates()

        assert templates == ["apple", "banana", "mountain", "zebra"]


class TestWorkflowTemplateManagerLoadTemplate:
    """Tests for loading individual templates."""

    def test_load_template_success(self, tmp_path: Path) -> None:
        """Test successfully loading a template."""
        # Create template file
        template = WorkflowTemplate(
            name="Test Template",
            description="A test template",
            category="character",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="test",
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )
        template.to_file(tmp_path / "test-template.json")

        manager = WorkflowTemplateManager(tmp_path)
        loaded = manager.load_template("test-template")

        assert loaded.name == "Test Template"
        assert loaded.description == "A test template"
        assert loaded.category == "character"
        assert "prompt" in loaded.parameters

    def test_load_template_not_found(self, tmp_path: Path) -> None:
        """Test loading non-existent template raises error."""
        manager = WorkflowTemplateManager(tmp_path)

        with pytest.raises(FileNotFoundError, match="Template not found"):
            manager.load_template("nonexistent")

    def test_load_template_caches_result(self, tmp_path: Path) -> None:
        """Test that loaded templates are cached."""
        template = WorkflowTemplate(
            name="Cached Template",
            description="Should be cached",
            parameters={},
            nodes={},
        )
        template.to_file(tmp_path / "cached.json")

        manager = WorkflowTemplateManager(tmp_path)

        # Load template twice
        first_load = manager.load_template("cached")
        second_load = manager.load_template("cached")

        # Should be the same object (cached)
        assert first_load is second_load

    def test_load_template_with_invalid_json_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid JSON raises appropriate error."""
        import json

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ this is not valid JSON }")

        manager = WorkflowTemplateManager(tmp_path)

        with pytest.raises(json.JSONDecodeError):
            manager.load_template("invalid")


class TestWorkflowTemplateManagerGetTemplate:
    """Tests for get_template method (alias for load_template)."""

    def test_get_template_loads_if_not_cached(self, tmp_path: Path) -> None:
        """Test that get_template loads template if not in cache."""
        template = WorkflowTemplate(
            name="Get Template", description="Test get method", parameters={}, nodes={}
        )
        template.to_file(tmp_path / "get-test.json")

        manager = WorkflowTemplateManager(tmp_path)
        loaded = manager.get_template("get-test")

        assert loaded.name == "Get Template"

    def test_get_template_returns_cached_if_available(self, tmp_path: Path) -> None:
        """Test that get_template returns cached template."""
        template = WorkflowTemplate(
            name="Cached", description="Should be cached", parameters={}, nodes={}
        )
        template.to_file(tmp_path / "cached.json")

        manager = WorkflowTemplateManager(tmp_path)

        # Pre-load
        first = manager.load_template("cached")
        # Get from cache
        second = manager.get_template("cached")

        assert first is second


class TestWorkflowTemplateManagerGetAllTemplates:
    """Tests for loading all templates at once."""

    def test_get_all_templates_empty_directory(self, tmp_path: Path) -> None:
        """Test getting all templates from empty directory."""
        manager = WorkflowTemplateManager(tmp_path)
        all_templates = manager.get_all_templates()

        assert all_templates == {}

    def test_get_all_templates_loads_all_files(self, tmp_path: Path) -> None:
        """Test that get_all_templates loads all template files."""
        # Create multiple templates
        for i in range(3):
            template = WorkflowTemplate(
                name=f"Template {i}",
                description=f"Description {i}",
                parameters={},
                nodes={},
            )
            template.to_file(tmp_path / f"template{i}.json")

        manager = WorkflowTemplateManager(tmp_path)
        all_templates = manager.get_all_templates()

        assert len(all_templates) == 3
        assert "template0" in all_templates
        assert "template1" in all_templates
        assert "template2" in all_templates

        assert all_templates["template0"].name == "Template 0"
        assert all_templates["template1"].name == "Template 1"
        assert all_templates["template2"].name == "Template 2"

    def test_get_all_templates_caches_results(self, tmp_path: Path) -> None:
        """Test that get_all_templates caches loaded templates."""
        template = WorkflowTemplate(
            name="Cache Test", description="Should be cached", parameters={}, nodes={}
        )
        template.to_file(tmp_path / "cache.json")

        manager = WorkflowTemplateManager(tmp_path)

        # Load all templates
        all_templates = manager.get_all_templates()

        # Load individual template - should be from cache
        cached = manager.get_template("cache")

        assert all_templates["cache"] is cached


class TestWorkflowTemplateManagerListByCategory:
    """Tests for filtering templates by category."""

    def test_list_by_category_character(self, tmp_path: Path) -> None:
        """Test listing templates in 'character' category."""
        # Create templates with different categories
        char_template = WorkflowTemplate(
            name="Character",
            description="Character template",
            category="character",
            parameters={},
            nodes={},
        )
        char_template.to_file(tmp_path / "character.json")

        item_template = WorkflowTemplate(
            name="Item",
            description="Item template",
            category="item",
            parameters={},
            nodes={},
        )
        item_template.to_file(tmp_path / "item.json")

        manager = WorkflowTemplateManager(tmp_path)
        character_templates = manager.list_templates_by_category("character")

        assert len(character_templates) == 1
        assert "character" in character_templates

    def test_list_by_category_multiple_matches(self, tmp_path: Path) -> None:
        """Test listing when multiple templates match category."""
        for i in range(3):
            template = WorkflowTemplate(
                name=f"Character {i}",
                description=f"Character template {i}",
                category="character",
                parameters={},
                nodes={},
            )
            template.to_file(tmp_path / f"char{i}.json")

        manager = WorkflowTemplateManager(tmp_path)
        character_templates = manager.list_templates_by_category("character")

        assert len(character_templates) == 3

    def test_list_by_category_no_matches(self, tmp_path: Path) -> None:
        """Test listing category with no matching templates."""
        template = WorkflowTemplate(
            name="Character",
            description="Character template",
            category="character",
            parameters={},
            nodes={},
        )
        template.to_file(tmp_path / "character.json")

        manager = WorkflowTemplateManager(tmp_path)
        environment_templates = manager.list_templates_by_category("environment")

        assert environment_templates == []

    def test_list_by_category_handles_none_category(self, tmp_path: Path) -> None:
        """Test listing templates with None category."""
        no_category_template = WorkflowTemplate(
            name="No Category",
            description="Template without category",
            category=None,
            parameters={},
            nodes={},
        )
        no_category_template.to_file(tmp_path / "no-category.json")

        char_template = WorkflowTemplate(
            name="Character",
            description="Character template",
            category="character",
            parameters={},
            nodes={},
        )
        char_template.to_file(tmp_path / "character.json")

        manager = WorkflowTemplateManager(tmp_path)

        # List with None should find template with category=None
        none_templates = manager.list_templates_by_category(None)
        assert len(none_templates) == 1
        assert "no-category" in none_templates


class TestWorkflowTemplateManagerReload:
    """Tests for reloading templates."""

    def test_reload_templates_clears_cache(self, tmp_path: Path) -> None:
        """Test that reload_templates clears the cache."""
        template = WorkflowTemplate(
            name="Original", description="Original template", parameters={}, nodes={}
        )
        template.to_file(tmp_path / "test.json")

        manager = WorkflowTemplateManager(tmp_path)

        # Load template
        original = manager.load_template("test")
        assert original.name == "Original"

        # Modify the file
        modified_template = WorkflowTemplate(
            name="Modified", description="Modified template", parameters={}, nodes={}
        )
        modified_template.to_file(tmp_path / "test.json")

        # Reload
        manager.reload_templates()

        # Load again - should get modified version
        reloaded = manager.load_template("test")
        assert reloaded.name == "Modified"
        assert reloaded is not original  # Should be different object

    def test_reload_templates_on_empty_cache(self, tmp_path: Path) -> None:
        """Test that reload works even when cache is empty."""
        manager = WorkflowTemplateManager(tmp_path)

        # Should not raise error
        manager.reload_templates()
        assert manager._templates == {}


class TestWorkflowTemplateManagerIntegration:
    """Integration tests for WorkflowTemplateManager."""

    def test_manager_with_real_templates(self, tmp_path: Path) -> None:
        """Test manager with realistic template structures."""
        # Create character portrait template
        char_template = WorkflowTemplate(
            name="Character Portrait",
            description="Generate character portraits",
            category="character",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Character description",
                    type="string",
                    default="a warrior",
                    required=True,
                ),
                "seed": TemplateParameter(
                    name="seed",
                    description="Random seed",
                    type="int",
                    default=-1,
                    required=False,
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                ),
                "2": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": "{{seed}}", "steps": 20, "cfg": 7.0},
                ),
            },
        )
        char_template.to_file(tmp_path / "character-portrait.json")

        # Create item icon template
        item_template = WorkflowTemplate(
            name="Item Icon",
            description="Generate item icons",
            category="item",
            parameters={
                "item": TemplateParameter(
                    name="item",
                    description="Item description",
                    type="string",
                    default="sword",
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{item}}, icon"}
                )
            },
        )
        item_template.to_file(tmp_path / "item-icon.json")

        manager = WorkflowTemplateManager(tmp_path)

        # List all templates
        all_template_ids = manager.list_templates()
        assert len(all_template_ids) == 2

        # List by category
        character_templates = manager.list_templates_by_category("character")
        assert len(character_templates) == 1

        item_templates = manager.list_templates_by_category("item")
        assert len(item_templates) == 1

        # Load and verify structure
        loaded_char = manager.get_template("character-portrait")
        assert len(loaded_char.parameters) == 2
        assert len(loaded_char.nodes) == 2

        loaded_item = manager.get_template("item-icon")
        assert len(loaded_item.parameters) == 1
        assert len(loaded_item.nodes) == 1

    def test_manager_workflow_from_template_to_instantiation(
        self, tmp_path: Path
    ) -> None:
        """Test complete workflow: list → load → instantiate."""
        template = WorkflowTemplate(
            name="Test Workflow",
            description="End-to-end test",
            category="character",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="default prompt",
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )
        template.to_file(tmp_path / "test.json")

        manager = WorkflowTemplateManager(tmp_path)

        # List templates
        templates = manager.list_templates()
        assert "test" in templates

        # Load template
        loaded = manager.load_template("test")

        # Instantiate workflow
        workflow = loaded.instantiate({"prompt": "custom prompt"})

        # Verify instantiation worked
        assert workflow.nodes["1"].inputs["text"] == "custom prompt"
