"""Tests for enhanced parameter substitution engine.

Tests comprehensive parameter substitution functionality including:
- Required parameter validation
- Type validation and coercion
- Complex nested structure substitution
- Error handling and messages
- Edge cases and boundary conditions
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from comfyui_mcp import TemplateParameter, WorkflowNode, WorkflowTemplate


class TestParameterSubstitutionBasics:
    """Tests for basic parameter substitution functionality."""

    def test_substitute_simple_string_parameter(self) -> None:
        """Test substituting a simple string parameter."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        workflow = template.instantiate({"prompt": "a wizard"})

        assert workflow.nodes["1"].inputs["text"] == "a wizard"

    def test_substitute_integer_parameter(self) -> None:
        """Test substituting an integer parameter."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "seed": TemplateParameter(
                    name="seed",
                    description="Random seed",
                    type="int",
                    default=42,
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(class_type="KSampler", inputs={"seed": "{{seed}}"})
            },
        )

        workflow = template.instantiate({"seed": 12345})

        assert workflow.nodes["1"].inputs["seed"] == 12345
        assert isinstance(workflow.nodes["1"].inputs["seed"], int)

    def test_substitute_float_parameter(self) -> None:
        """Test substituting a float parameter."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "cfg": TemplateParameter(
                    name="cfg",
                    description="CFG scale",
                    type="float",
                    default=7.0,
                    required=False,
                )
            },
            nodes={"1": WorkflowNode(class_type="KSampler", inputs={"cfg": "{{cfg}}"})},
        )

        workflow = template.instantiate({"cfg": 8.5})

        assert workflow.nodes["1"].inputs["cfg"] == 8.5
        assert isinstance(workflow.nodes["1"].inputs["cfg"], float)

    def test_substitute_multiple_parameters(self) -> None:
        """Test substituting multiple parameters in same template."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="",
                    required=True,
                ),
                "seed": TemplateParameter(
                    name="seed",
                    description="Random seed",
                    type="int",
                    default=-1,
                    required=False,
                ),
                "steps": TemplateParameter(
                    name="steps",
                    description="Sampling steps",
                    type="int",
                    default=20,
                    required=False,
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                ),
                "2": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": "{{seed}}", "steps": "{{steps}}"},
                ),
            },
        )

        workflow = template.instantiate({"prompt": "test", "seed": 123, "steps": 30})

        assert workflow.nodes["1"].inputs["text"] == "test"
        assert workflow.nodes["2"].inputs["seed"] == 123
        assert workflow.nodes["2"].inputs["steps"] == 30


class TestRequiredParameterValidation:
    """Tests for required parameter validation."""

    def test_missing_required_parameter_raises_error(self) -> None:
        """Test that missing required parameter with None default raises ValidationError."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default=None,  # None default means truly required
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        with pytest.raises(ValidationError, match="prompt"):
            template.instantiate({})

    def test_none_value_for_required_parameter_raises_error(self) -> None:
        """Test that None value for required parameter raises error."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="default",
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        with pytest.raises(ValidationError, match="prompt"):
            template.instantiate({"prompt": None})

    def test_empty_string_for_required_string_parameter_raises_error(self) -> None:
        """Test that empty string for required parameter raises error."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="default",
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        # Empty strings raise ValueError (consistent with type validation)
        with pytest.raises(ValueError, match="prompt.*empty"):
            template.instantiate({"prompt": ""})

    def test_multiple_missing_required_parameters_lists_all(self) -> None:
        """Test that multiple missing required parameters with None defaults are all listed."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default=None,  # None default means truly required
                    required=True,
                ),
                "negative": TemplateParameter(
                    name="negative",
                    description="Negative prompt",
                    type="string",
                    default=None,  # None default means truly required
                    required=True,
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            template.instantiate({})

        error_message = str(exc_info.value)
        assert "prompt" in error_message
        assert "negative" in error_message

    def test_optional_parameter_can_be_omitted(self) -> None:
        """Test that optional parameters can be omitted and use defaults."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="a character",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        workflow = template.instantiate({})

        assert workflow.nodes["1"].inputs["text"] == "a character"


class TestTypeValidation:
    """Tests for parameter type validation."""

    def test_string_to_int_type_mismatch_raises_error(self) -> None:
        """Test that providing string for int parameter raises error."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "seed": TemplateParameter(
                    name="seed",
                    description="Random seed",
                    type="int",
                    default=42,
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(class_type="KSampler", inputs={"seed": "{{seed}}"})
            },
        )

        with pytest.raises((ValidationError, ValueError), match="seed.*int"):
            template.instantiate({"seed": "not a number"})

    def test_int_to_string_type_coercion_allowed(self) -> None:
        """Test that int can be coerced to string."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "value": TemplateParameter(
                    name="value",
                    description="String value",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={"1": WorkflowNode(class_type="Test", inputs={"text": "{{value}}"})},
        )

        workflow = template.instantiate({"value": 123})

        assert workflow.nodes["1"].inputs["text"] == "123"

    def test_numeric_string_to_int_coercion_allowed(self) -> None:
        """Test that numeric string can be coerced to int."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "seed": TemplateParameter(
                    name="seed",
                    description="Random seed",
                    type="int",
                    default=42,
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(class_type="KSampler", inputs={"seed": "{{seed}}"})
            },
        )

        workflow = template.instantiate({"seed": "12345"})

        assert workflow.nodes["1"].inputs["seed"] == 12345
        assert isinstance(workflow.nodes["1"].inputs["seed"], int)

    def test_numeric_string_to_float_coercion_allowed(self) -> None:
        """Test that numeric string can be coerced to float."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "cfg": TemplateParameter(
                    name="cfg",
                    description="CFG scale",
                    type="float",
                    default=7.0,
                    required=False,
                )
            },
            nodes={"1": WorkflowNode(class_type="KSampler", inputs={"cfg": "{{cfg}}"})},
        )

        workflow = template.instantiate({"cfg": "8.5"})

        assert workflow.nodes["1"].inputs["cfg"] == 8.5
        assert isinstance(workflow.nodes["1"].inputs["cfg"], float)

    def test_int_to_float_coercion_allowed(self) -> None:
        """Test that int can be coerced to float."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "cfg": TemplateParameter(
                    name="cfg",
                    description="CFG scale",
                    type="float",
                    default=7.0,
                    required=False,
                )
            },
            nodes={"1": WorkflowNode(class_type="KSampler", inputs={"cfg": "{{cfg}}"})},
        )

        workflow = template.instantiate({"cfg": 8})

        assert workflow.nodes["1"].inputs["cfg"] == 8.0
        assert isinstance(workflow.nodes["1"].inputs["cfg"], float)

    def test_list_for_string_parameter_raises_error(self) -> None:
        """Test that list for string parameter raises error."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        with pytest.raises((ValidationError, ValueError), match="prompt.*string"):
            template.instantiate({"prompt": ["item1", "item2"]})


class TestNestedStructureSubstitution:
    """Tests for substituting parameters in nested structures."""

    def test_substitute_in_nested_dict(self) -> None:
        """Test parameter substitution in nested dictionaries."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "value": TemplateParameter(
                    name="value",
                    description="Test value",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="Test",
                    inputs={"nested": {"inner": {"value": "{{value}}"}}},
                )
            },
        )

        workflow = template.instantiate({"value": "test"})

        assert workflow.nodes["1"].inputs["nested"]["inner"]["value"] == "test"

    def test_substitute_in_list(self) -> None:
        """Test parameter substitution in lists."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "item": TemplateParameter(
                    name="item",
                    description="List item",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="Test", inputs={"items": ["first", "{{item}}", "third"]}
                )
            },
        )

        workflow = template.instantiate({"item": "second"})

        assert workflow.nodes["1"].inputs["items"] == ["first", "second", "third"]

    def test_substitute_in_list_of_dicts(self) -> None:
        """Test parameter substitution in list of dictionaries."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "name": TemplateParameter(
                    name="name",
                    description="Name value",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="Test",
                    inputs={"objects": [{"name": "{{name}}"}, {"name": "static"}]},
                )
            },
        )

        workflow = template.instantiate({"name": "dynamic"})

        assert workflow.nodes["1"].inputs["objects"][0]["name"] == "dynamic"
        assert workflow.nodes["1"].inputs["objects"][1]["name"] == "static"


class TestPartialStringSubstitution:
    """Tests for partial string substitution (interpolation)."""

    def test_partial_string_substitution(self) -> None:
        """Test substituting parameter within a larger string."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "subject": TemplateParameter(
                    name="subject",
                    description="Subject",
                    type="string",
                    default="character",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode",
                    inputs={"text": "a detailed portrait of {{subject}}, 4k"},
                )
            },
        )

        workflow = template.instantiate({"subject": "a wizard"})

        assert (
            workflow.nodes["1"].inputs["text"] == "a detailed portrait of a wizard, 4k"
        )

    def test_multiple_placeholders_in_same_string(self) -> None:
        """Test multiple placeholders in the same string."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "subject": TemplateParameter(
                    name="subject",
                    description="Subject",
                    type="string",
                    default="character",
                    required=False,
                ),
                "style": TemplateParameter(
                    name="style",
                    description="Art style",
                    type="string",
                    default="realistic",
                    required=False,
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode",
                    inputs={"text": "{{subject}}, {{style}} style"},
                )
            },
        )

        workflow = template.instantiate({"subject": "warrior", "style": "anime"})

        assert workflow.nodes["1"].inputs["text"] == "warrior, anime style"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_nodes_dict(self) -> None:
        """Test template with no nodes."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={},
            nodes={},
        )

        workflow = template.instantiate({})

        assert workflow.nodes == {}

    def test_no_parameters(self) -> None:
        """Test template with no parameters."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={},
            nodes={"1": WorkflowNode(class_type="Test", inputs={"value": "static"})},
        )

        workflow = template.instantiate({})

        assert workflow.nodes["1"].inputs["value"] == "static"

    def test_unused_parameter_in_params_dict(self) -> None:
        """Test that unused parameters in params dict don't cause errors."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "used": TemplateParameter(
                    name="used",
                    description="Used param",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={"1": WorkflowNode(class_type="Test", inputs={"value": "{{used}}"})},
        )

        workflow = template.instantiate({"used": "value", "unused": "ignored"})

        assert workflow.nodes["1"].inputs["value"] == "value"

    def test_parameter_not_in_template_definition_raises_warning(self) -> None:
        """Test that using undefined parameter raises warning."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={},
            nodes={
                "1": WorkflowNode(class_type="Test", inputs={"value": "{{undefined}}"})
            },
        )

        # Should keep placeholder if parameter not defined
        workflow = template.instantiate({})

        assert workflow.nodes["1"].inputs["value"] == "{{undefined}}"

    def test_special_characters_in_string_values(self) -> None:
        """Test that special characters in values are handled correctly."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="default",
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        special_chars = 'Test with {{curly}}, (parens), [brackets], and "quotes"'
        workflow = template.instantiate({"prompt": special_chars})

        assert workflow.nodes["1"].inputs["text"] == special_chars

    def test_numeric_zero_values(self) -> None:
        """Test that zero values are handled correctly."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "seed": TemplateParameter(
                    name="seed",
                    description="Random seed",
                    type="int",
                    default=-1,
                    required=False,
                ),
                "cfg": TemplateParameter(
                    name="cfg",
                    description="CFG scale",
                    type="float",
                    default=7.0,
                    required=False,
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": "{{seed}}", "cfg": "{{cfg}}"},
                )
            },
        )

        workflow = template.instantiate({"seed": 0, "cfg": 0.0})

        assert workflow.nodes["1"].inputs["seed"] == 0
        assert workflow.nodes["1"].inputs["cfg"] == 0.0


class TestErrorMessages:
    """Tests for error message quality and helpfulness."""

    def test_missing_required_param_error_includes_param_name(self) -> None:
        """Test that error for missing required param includes parameter name."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default=None,  # None default means truly required
                    required=True,
                )
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            template.instantiate({})

        assert "prompt" in str(exc_info.value)

    def test_type_error_includes_param_name_and_expected_type(self) -> None:
        """Test that type error includes param name and expected type."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "seed": TemplateParameter(
                    name="seed",
                    description="Random seed",
                    type="int",
                    default=42,
                    required=False,
                )
            },
            nodes={
                "1": WorkflowNode(class_type="KSampler", inputs={"seed": "{{seed}}"})
            },
        )

        with pytest.raises((ValidationError, ValueError)) as exc_info:
            template.instantiate({"seed": "not_a_number"})

        error_msg = str(exc_info.value)
        assert "seed" in error_msg
        assert "int" in error_msg.lower()
