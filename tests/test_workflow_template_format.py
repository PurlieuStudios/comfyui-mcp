"""Tests for workflow template JSON file format.

Tests the JSON serialization and deserialization of workflow templates including:
- Saving templates to JSON files
- Loading templates from JSON files
- JSON schema validation
- Parameter and node structure preservation
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from comfyui_mcp import TemplateParameter, WorkflowNode, WorkflowTemplate


class TestWorkflowTemplateToFile:
    """Tests for WorkflowTemplate.to_file() method."""

    def test_to_file_creates_valid_json(self, tmp_path: Path) -> None:
        """Test that to_file creates a valid JSON file."""
        template = WorkflowTemplate(
            name="Test Template",
            description="A test template",
            category="character",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="a warrior",
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        output_file = tmp_path / "template.json"
        template.to_file(output_file)

        assert output_file.exists()
        assert output_file.is_file()

        # Verify it's valid JSON
        with open(output_file) as f:
            data = json.load(f)
            assert data["name"] == "Test Template"
            assert data["description"] == "A test template"
            assert data["category"] == "character"

    def test_to_file_preserves_all_fields(self, tmp_path: Path) -> None:
        """Test that to_file preserves all template fields."""
        template = WorkflowTemplate(
            name="Complex Template",
            description="Template with multiple parameters",
            category="item",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="sword",
                    required=True,
                ),
                "width": TemplateParameter(
                    name="width",
                    description="Image width",
                    type="int",
                    default=512,
                    required=False,
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
                    class_type="EmptyLatentImage",
                    inputs={"width": "{{width}}", "height": 512, "batch_size": 1},
                ),
                "2": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                ),
            },
        )

        output_file = tmp_path / "complex.json"
        template.to_file(output_file)

        with open(output_file) as f:
            data = json.load(f)

        # Check all fields are present
        assert data["name"] == "Complex Template"
        assert data["description"] == "Template with multiple parameters"
        assert data["category"] == "item"
        assert len(data["parameters"]) == 3
        assert len(data["nodes"]) == 2

        # Check parameter structure
        assert data["parameters"]["prompt"]["name"] == "prompt"
        assert data["parameters"]["prompt"]["type"] == "string"
        assert data["parameters"]["prompt"]["default"] == "sword"
        assert data["parameters"]["prompt"]["required"] is True

        # Check node structure
        assert data["nodes"]["1"]["class_type"] == "EmptyLatentImage"
        assert data["nodes"]["1"]["inputs"]["width"] == "{{width}}"

    def test_to_file_handles_no_category(self, tmp_path: Path) -> None:
        """Test that to_file correctly handles None category."""
        template = WorkflowTemplate(
            name="No Category",
            description="Template without category",
            category=None,
            parameters={},
            nodes={},
        )

        output_file = tmp_path / "no_category.json"
        template.to_file(output_file)

        with open(output_file) as f:
            data = json.load(f)

        assert data["category"] is None

    def test_to_file_overwrites_existing_file(self, tmp_path: Path) -> None:
        """Test that to_file overwrites existing files."""
        output_file = tmp_path / "overwrite.json"
        output_file.write_text('{"old": "data"}')

        template = WorkflowTemplate(
            name="New Template",
            description="Should overwrite",
            parameters={},
            nodes={},
        )

        template.to_file(output_file)

        with open(output_file) as f:
            data = json.load(f)

        assert "old" not in data
        assert data["name"] == "New Template"


class TestWorkflowTemplateFromFile:
    """Tests for WorkflowTemplate.from_file() classmethod."""

    def test_from_file_loads_valid_template(self, tmp_path: Path) -> None:
        """Test loading a valid template from JSON file."""
        template_data = {
            "name": "Character Portrait",
            "description": "Generate character portraits",
            "category": "character",
            "parameters": {
                "prompt": {
                    "name": "prompt",
                    "description": "Character description",
                    "type": "string",
                    "default": "a warrior",
                    "required": True,
                }
            },
            "nodes": {
                "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "{{prompt}}"}}
            },
        }

        template_file = tmp_path / "character.json"
        with open(template_file, "w") as f:
            json.dump(template_data, f)

        template = WorkflowTemplate.from_file(template_file)

        assert template.name == "Character Portrait"
        assert template.description == "Generate character portraits"
        assert template.category == "character"
        assert len(template.parameters) == 1
        assert "prompt" in template.parameters
        assert template.parameters["prompt"].default == "a warrior"
        assert len(template.nodes) == 1
        assert "1" in template.nodes

    def test_from_file_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Test that from_file raises FileNotFoundError for missing files."""
        missing_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            WorkflowTemplate.from_file(missing_file)

    def test_from_file_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """Test that from_file raises error for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ this is not valid JSON }")

        with pytest.raises(json.JSONDecodeError):
            WorkflowTemplate.from_file(invalid_file)

    def test_from_file_raises_on_missing_required_fields(self, tmp_path: Path) -> None:
        """Test that from_file raises ValidationError for missing required fields."""
        incomplete_data = {
            "name": "Incomplete",
            # Missing description, parameters, nodes
        }

        template_file = tmp_path / "incomplete.json"
        with open(template_file, "w") as f:
            json.dump(incomplete_data, f)

        with pytest.raises(ValidationError):
            WorkflowTemplate.from_file(template_file)

    def test_from_file_handles_complex_nodes(self, tmp_path: Path) -> None:
        """Test loading templates with complex node structures."""
        template_data = {
            "name": "Complex Workflow",
            "description": "Workflow with connections",
            "category": "environment",
            "parameters": {},
            "nodes": {
                "1": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "model.safetensors"},
                },
                "2": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": "landscape", "clip": ["1", 1]},
                },
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": 42,
                        "steps": 20,
                        "cfg": 7.0,
                        "model": ["1", 0],
                        "positive": ["2", 0],
                    },
                },
            },
        }

        template_file = tmp_path / "complex.json"
        with open(template_file, "w") as f:
            json.dump(template_data, f)

        template = WorkflowTemplate.from_file(template_file)

        assert len(template.nodes) == 3
        assert template.nodes["2"].inputs["clip"] == ["1", 1]
        assert template.nodes["3"].inputs["model"] == ["1", 0]
        assert template.nodes["3"].inputs["seed"] == 42


class TestWorkflowTemplateRoundTrip:
    """Tests for round-trip serialization (to_file → from_file)."""

    def test_roundtrip_preserves_template(self, tmp_path: Path) -> None:
        """Test that saving and loading preserves template exactly."""
        original = WorkflowTemplate(
            name="Round Trip Test",
            description="Template for round-trip testing",
            category="specialized",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="test",
                    required=True,
                ),
                "steps": TemplateParameter(
                    name="steps",
                    description="Number of steps",
                    type="int",
                    default=20,
                    required=False,
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": 42, "steps": "{{steps}}", "cfg": 7.0},
                )
            },
        )

        template_file = tmp_path / "roundtrip.json"
        original.to_file(template_file)
        loaded = WorkflowTemplate.from_file(template_file)

        # Verify all fields match
        assert loaded.name == original.name
        assert loaded.description == original.description
        assert loaded.category == original.category
        assert len(loaded.parameters) == len(original.parameters)
        assert len(loaded.nodes) == len(original.nodes)

        # Check parameters in detail
        for param_name, param in original.parameters.items():
            loaded_param = loaded.parameters[param_name]
            assert loaded_param.name == param.name
            assert loaded_param.description == param.description
            assert loaded_param.type == param.type
            assert loaded_param.default == param.default
            assert loaded_param.required == param.required

        # Check nodes in detail
        for node_id, node in original.nodes.items():
            loaded_node = loaded.nodes[node_id]
            assert loaded_node.class_type == node.class_type
            assert loaded_node.inputs == node.inputs

    def test_roundtrip_with_empty_parameters(self, tmp_path: Path) -> None:
        """Test round-trip with empty parameters dict."""
        original = WorkflowTemplate(
            name="No Params",
            description="Template with no parameters",
            parameters={},
            nodes={
                "1": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "model.safetensors"},
                )
            },
        )

        template_file = tmp_path / "no_params.json"
        original.to_file(template_file)
        loaded = WorkflowTemplate.from_file(template_file)

        assert len(loaded.parameters) == 0
        assert len(loaded.nodes) == 1


class TestWorkflowTemplateJSONFormat:
    """Tests for the JSON file format structure."""

    def test_json_format_has_correct_top_level_keys(self, tmp_path: Path) -> None:
        """Test that JSON format has all required top-level keys."""
        template = WorkflowTemplate(
            name="Format Test",
            description="Testing JSON format",
            category="item",
            parameters={},
            nodes={},
        )

        output_file = tmp_path / "format.json"
        template.to_file(output_file)

        with open(output_file) as f:
            data = json.load(f)

        required_keys = {"name", "description", "category", "parameters", "nodes"}
        assert set(data.keys()) == required_keys

    def test_json_format_uses_pretty_printing(self, tmp_path: Path) -> None:
        """Test that JSON files are pretty-printed (indented)."""
        template = WorkflowTemplate(
            name="Pretty Print",
            description="Test pretty printing",
            parameters={},
            nodes={},
        )

        output_file = tmp_path / "pretty.json"
        template.to_file(output_file)

        content = output_file.read_text()

        # Pretty-printed JSON should have newlines and indentation
        assert "\n" in content
        assert "  " in content or "\t" in content

    def test_parameter_json_structure(self, tmp_path: Path) -> None:
        """Test that parameters are serialized with correct structure."""
        template = WorkflowTemplate(
            name="Param Structure",
            description="Test parameter structure",
            parameters={
                "test_param": TemplateParameter(
                    name="test_param",
                    description="A test parameter",
                    type="float",
                    default=3.14,
                    required=False,
                )
            },
            nodes={},
        )

        output_file = tmp_path / "param_structure.json"
        template.to_file(output_file)

        with open(output_file) as f:
            data = json.load(f)

        param_data = data["parameters"]["test_param"]
        required_param_keys = {"name", "description", "type", "default", "required"}
        assert set(param_data.keys()) == required_param_keys
        assert param_data["name"] == "test_param"
        assert param_data["type"] == "float"
        assert param_data["default"] == 3.14
        assert param_data["required"] is False

    def test_node_json_structure(self, tmp_path: Path) -> None:
        """Test that nodes are serialized with correct structure."""
        template = WorkflowTemplate(
            name="Node Structure",
            description="Test node structure",
            parameters={},
            nodes={
                "1": WorkflowNode(
                    class_type="TestNode",
                    inputs={"param1": "value1", "param2": 42, "param3": ["ref", 0]},
                )
            },
        )

        output_file = tmp_path / "node_structure.json"
        template.to_file(output_file)

        with open(output_file) as f:
            data = json.load(f)

        node_data = data["nodes"]["1"]
        assert set(node_data.keys()) == {"class_type", "inputs"}
        assert node_data["class_type"] == "TestNode"
        assert node_data["inputs"]["param1"] == "value1"
        assert node_data["inputs"]["param2"] == 42
        assert node_data["inputs"]["param3"] == ["ref", 0]
