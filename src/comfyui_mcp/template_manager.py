"""Workflow template management for ComfyUI MCP Server.

This module provides WorkflowTemplateManager for managing collections of
workflow templates, including loading from files, caching, and filtering.

Example:
    >>> from comfyui_mcp.template_manager import WorkflowTemplateManager
    >>> from pathlib import Path
    >>>
    >>> # Initialize manager with template directory
    >>> manager = WorkflowTemplateManager("workflows/")
    >>>
    >>> # List all available templates
    >>> template_ids = manager.list_templates()
    >>> print(f"Available templates: {template_ids}")
    >>>
    >>> # Load a specific template
    >>> template = manager.load_template("character-portrait")
    >>> workflow = template.instantiate({"prompt": "a wizard"})
    >>>
    >>> # Filter by category
    >>> character_templates = manager.list_templates_by_category("character")
"""

from __future__ import annotations

from pathlib import Path

from comfyui_mcp.models import WorkflowTemplate


class WorkflowTemplateManager:
    """Manages a collection of workflow templates from a directory.

    The WorkflowTemplateManager handles loading, caching, and filtering of
    workflow templates stored as JSON files in a directory. Templates are
    identified by their filename (without the .json extension).

    Attributes:
        template_dir: Path to the directory containing template files
        _templates: Internal cache of loaded templates (dict[template_id, WorkflowTemplate])

    Example:
        >>> manager = WorkflowTemplateManager("workflows/")
        >>>
        >>> # List all templates
        >>> all_templates = manager.list_templates()
        >>> print(f"Found {len(all_templates)} templates")
        >>>
        >>> # Load a specific template
        >>> template = manager.load_template("character-portrait")
        >>> print(f"Loaded: {template.name}")
        >>>
        >>> # Filter by category
        >>> character_templates = manager.list_templates_by_category("character")
    """

    def __init__(self, template_dir: Path | str) -> None:
        """Initialize the template manager.

        Args:
            template_dir: Path to directory containing template JSON files.
                         Can be a Path object or string path.

        Raises:
            FileNotFoundError: If template_dir doesn't exist
            ValueError: If template_dir is not a directory

        Example:
            >>> manager = WorkflowTemplateManager("workflows/")
            >>> # or
            >>> from pathlib import Path
            >>> manager = WorkflowTemplateManager(Path("workflows"))
        """
        if isinstance(template_dir, str):
            template_dir = Path(template_dir)

        if not template_dir.exists():
            msg = f"Template directory not found: {template_dir}"
            raise FileNotFoundError(msg)

        if not template_dir.is_dir():
            msg = f"Template directory must be a directory, not a file: {template_dir}"
            raise ValueError(msg)

        self.template_dir: Path = template_dir
        self._templates: dict[str, WorkflowTemplate] = {}

    def list_templates(self) -> list[str]:
        """List all available template IDs in the directory.

        Scans the template directory for .json files and returns their IDs
        (filenames without the .json extension). Results are sorted alphabetically.

        Returns:
            List of template IDs (filenames without .json), sorted alphabetically.
            Empty list if no templates found.

        Example:
            >>> manager = WorkflowTemplateManager("workflows/")
            >>> templates = manager.list_templates()
            >>> print(templates)
            ['character-portrait', 'item-icon', 'environment-texture']
        """
        template_files = self.template_dir.glob("*.json")
        template_ids = [f.stem for f in template_files]
        return sorted(template_ids)

    def load_template(self, template_id: str) -> WorkflowTemplate:
        """Load a template by its ID.

        Loads a template from disk and caches it for future use. If the template
        is already cached, returns the cached version.

        Args:
            template_id: Template identifier (filename without .json extension)

        Returns:
            Loaded WorkflowTemplate instance

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValidationError: If template file contains invalid data
            JSONDecodeError: If template file contains invalid JSON

        Example:
            >>> manager = WorkflowTemplateManager("workflows/")
            >>> template = manager.load_template("character-portrait")
            >>> print(f"Loaded: {template.name}")
            Loaded: Character Portrait Generator
        """
        # Check cache first
        if template_id in self._templates:
            return self._templates[template_id]

        # Load from file
        template_path = self.template_dir / f"{template_id}.json"

        if not template_path.exists():
            msg = f"Template not found: {template_id}"
            raise FileNotFoundError(msg)

        # Load and cache
        template = WorkflowTemplate.from_file(template_path)
        self._templates[template_id] = template

        return template

    def get_template(self, template_id: str) -> WorkflowTemplate:
        """Get a template by its ID (alias for load_template).

        This method is an alias for load_template() to provide a more natural
        API for retrieving templates.

        Args:
            template_id: Template identifier (filename without .json extension)

        Returns:
            Loaded WorkflowTemplate instance

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValidationError: If template file contains invalid data
            JSONDecodeError: If template file contains invalid JSON

        Example:
            >>> manager = WorkflowTemplateManager("workflows/")
            >>> template = manager.get_template("item-icon")
            >>> workflow = template.instantiate({"item": "sword"})
        """
        return self.load_template(template_id)

    def get_all_templates(self) -> dict[str, WorkflowTemplate]:
        """Load and return all templates as a dictionary.

        Loads all template files in the directory and returns them as a dictionary
        mapping template IDs to WorkflowTemplate instances. Caches all loaded
        templates for future use.

        Returns:
            Dictionary mapping template IDs to WorkflowTemplate instances.
            Empty dict if no templates found.

        Example:
            >>> manager = WorkflowTemplateManager("workflows/")
            >>> all_templates = manager.get_all_templates()
            >>> for template_id, template in all_templates.items():
            ...     print(f"{template_id}: {template.name}")
            character-portrait: Character Portrait Generator
            item-icon: Item Icon Generator
        """
        template_ids = self.list_templates()

        for template_id in template_ids:
            # Load each template (will use cache if already loaded)
            self.load_template(template_id)

        # Return copy of cache
        return dict(self._templates)

    def list_templates_by_category(self, category: str | None) -> list[str]:
        """List templates filtered by category.

        Loads all templates and filters by the specified category. Templates
        are loaded and cached during this operation.

        Args:
            category: Category to filter by (e.g., "character", "item", "environment"),
                     or None to find templates with no category

        Returns:
            List of template IDs matching the category, sorted alphabetically.
            Empty list if no templates match.

        Example:
            >>> manager = WorkflowTemplateManager("workflows/")
            >>> character_templates = manager.list_templates_by_category("character")
            >>> print(character_templates)
            ['character-portrait', 'npc-portrait']
            >>>
            >>> # Find templates without a category
            >>> uncategorized = manager.list_templates_by_category(None)
        """
        # Load all templates to check categories
        all_templates = self.get_all_templates()

        # Filter by category
        matching_ids = [
            template_id
            for template_id, template in all_templates.items()
            if template.category == category
        ]

        return sorted(matching_ids)

    def reload_templates(self) -> None:
        """Clear the template cache and reload all templates.

        Clears the internal cache of loaded templates. The next call to
        load_template() or get_template() will load fresh data from disk.

        This is useful when template files have been modified on disk and
        you want to reload the updated versions.

        Example:
            >>> manager = WorkflowTemplateManager("workflows/")
            >>> template = manager.load_template("test")
            >>> print(template.name)
            Original Name
            >>>
            >>> # Template file is modified externally
            >>> manager.reload_templates()
            >>>
            >>> # Load fresh version
            >>> template = manager.load_template("test")
            >>> print(template.name)
            Updated Name
        """
        self._templates.clear()


__all__ = ["WorkflowTemplateManager"]
