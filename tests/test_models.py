"""Tests for comfyui_mcp.models module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from comfyui_mcp.models import (
    GenerationRequest,
    GenerationResult,
    TemplateParameter,
    WorkflowNode,
    WorkflowPrompt,
    WorkflowTemplate,
)


class TestWorkflowNode:
    """Tests for WorkflowNode model."""

    def test_create_simple_node(self) -> None:
        """Test creating a simple workflow node with basic inputs."""
        node = WorkflowNode(
            class_type="CheckpointLoaderSimple",
            inputs={"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
        )

        assert node.class_type == "CheckpointLoaderSimple"
        assert node.inputs["ckpt_name"] == "v1-5-pruned-emaonly.safetensors"

    def test_create_node_with_connections(self) -> None:
        """Test creating a node with input connections to other nodes."""
        node = WorkflowNode(
            class_type="KSampler",
            inputs={
                "cfg": 8,
                "denoise": 1.0,
                "seed": 123456,
                "steps": 20,
                "sampler_name": "euler",
                "scheduler": "normal",
                "model": ["4", 0],  # Connection to node "4", output slot 0
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        )

        assert node.class_type == "KSampler"
        assert node.inputs["seed"] == 123456
        assert node.inputs["model"] == ["4", 0]
        assert isinstance(node.inputs["model"], list)

    def test_create_node_with_mixed_input_types(self) -> None:
        """Test node with various input types (int, float, str, bool, list)."""
        node = WorkflowNode(
            class_type="TestNode",
            inputs={
                "int_param": 42,
                "float_param": 3.14,
                "str_param": "test",
                "bool_param": True,
                "connection": ["node_id", 0],
                "nested_dict": {"key": "value"},
            },
        )

        assert node.inputs["int_param"] == 42
        assert node.inputs["float_param"] == 3.14
        assert node.inputs["str_param"] == "test"
        assert node.inputs["bool_param"] is True
        assert node.inputs["connection"] == ["node_id", 0]
        assert node.inputs["nested_dict"] == {"key": "value"}

    def test_node_requires_class_type(self) -> None:
        """Test that class_type is required."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowNode(inputs={})  # type: ignore

        assert "class_type" in str(exc_info.value)

    def test_node_requires_inputs(self) -> None:
        """Test that inputs is required."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowNode(class_type="TestNode")  # type: ignore

        assert "inputs" in str(exc_info.value)

    def test_node_serialization(self) -> None:
        """Test that node can be serialized to dict/JSON."""
        node = WorkflowNode(
            class_type="KSampler",
            inputs={"seed": 123, "model": ["4", 0]},
        )

        data = node.model_dump()
        assert data == {
            "class_type": "KSampler",
            "inputs": {"seed": 123, "model": ["4", 0]},
        }


class TestWorkflowPrompt:
    """Tests for WorkflowPrompt model."""

    def test_create_empty_workflow(self) -> None:
        """Test creating an empty workflow prompt."""
        prompt = WorkflowPrompt(nodes={})

        assert prompt.nodes == {}
        assert prompt.client_id is None

    def test_create_workflow_with_single_node(self) -> None:
        """Test creating a workflow with a single node."""
        prompt = WorkflowPrompt(
            nodes={
                "4": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
                )
            }
        )

        assert "4" in prompt.nodes
        assert prompt.nodes["4"].class_type == "CheckpointLoaderSimple"

    def test_create_workflow_with_multiple_nodes(self) -> None:
        """Test creating a workflow with multiple connected nodes."""
        prompt = WorkflowPrompt(
            nodes={
                "4": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "model.safetensors"},
                ),
                "6": WorkflowNode(
                    class_type="CLIPTextEncode",
                    inputs={"text": "a beautiful landscape", "clip": ["4", 1]},
                ),
                "3": WorkflowNode(
                    class_type="KSampler",
                    inputs={
                        "seed": 987654,
                        "steps": 20,
                        "cfg": 8.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                    },
                ),
            }
        )

        assert len(prompt.nodes) == 3
        assert "4" in prompt.nodes
        assert "6" in prompt.nodes
        assert "3" in prompt.nodes

    def test_workflow_with_client_id(self) -> None:
        """Test workflow with optional client_id."""
        prompt = WorkflowPrompt(
            nodes={"1": WorkflowNode(class_type="Test", inputs={})},
            client_id="test-client-123",
        )

        assert prompt.client_id == "test-client-123"

    def test_workflow_serialization(self) -> None:
        """Test that workflow can be serialized to the ComfyUI API format."""
        prompt = WorkflowPrompt(
            nodes={
                "3": WorkflowNode(
                    class_type="KSampler",
                    inputs={
                        "seed": 8566257,
                        "steps": 20,
                        "cfg": 8,
                        "model": ["4", 0],
                    },
                ),
                "4": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
                ),
            },
            client_id="my-client",
        )

        data = prompt.model_dump()

        # Check structure matches ComfyUI API format
        assert "nodes" in data
        assert "client_id" in data
        assert data["client_id"] == "my-client"
        assert "3" in data["nodes"]
        assert "4" in data["nodes"]
        assert data["nodes"]["3"]["class_type"] == "KSampler"
        assert data["nodes"]["3"]["inputs"]["seed"] == 8566257

    def test_workflow_to_api_format(self) -> None:
        """Test conversion to ComfyUI API /prompt format."""
        prompt = WorkflowPrompt(
            nodes={"1": WorkflowNode(class_type="Test", inputs={"param": "value"})},
            client_id="client-123",
        )

        api_format = prompt.to_api_format()

        assert "prompt" in api_format
        assert "client_id" in api_format
        assert api_format["client_id"] == "client-123"
        assert "1" in api_format["prompt"]
        assert api_format["prompt"]["1"]["class_type"] == "Test"

    def test_workflow_from_dict(self) -> None:
        """Test creating workflow from dictionary (parsing API response)."""
        data = {
            "nodes": {
                "1": {
                    "class_type": "KSampler",
                    "inputs": {"seed": 123, "model": ["2", 0]},
                }
            },
            "client_id": "test",
        }

        prompt = WorkflowPrompt(**data)  # type: ignore[arg-type]

        assert prompt.client_id == "test"
        assert "1" in prompt.nodes
        assert prompt.nodes["1"].class_type == "KSampler"

    def test_workflow_seed_extraction(self) -> None:
        """Test extracting seed value from KSampler nodes."""
        prompt = WorkflowPrompt(
            nodes={
                "3": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": 42, "steps": 20},
                ),
                "4": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "model.safetensors"},
                ),
            }
        )

        seed = prompt.get_seed()
        assert seed == 42

    def test_workflow_seed_extraction_no_ksampler(self) -> None:
        """Test seed extraction when no KSampler node exists."""
        prompt = WorkflowPrompt(
            nodes={
                "1": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "model.safetensors"},
                )
            }
        )

        seed = prompt.get_seed()
        assert seed is None

    def test_workflow_set_seed(self) -> None:
        """Test updating seed in all KSampler nodes."""
        prompt = WorkflowPrompt(
            nodes={
                "3": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": 123, "steps": 20},
                ),
                "5": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": 456, "steps": 30},
                ),
            }
        )

        prompt.set_seed(999)

        assert prompt.nodes["3"].inputs["seed"] == 999
        assert prompt.nodes["5"].inputs["seed"] == 999


class TestTemplateParameter:
    """Tests for TemplateParameter model."""

    def test_create_string_parameter(self) -> None:
        """Test creating a string template parameter."""
        param = TemplateParameter(
            name="prompt",
            description="Text prompt for generation",
            type="string",
            default="a beautiful landscape",
        )

        assert param.name == "prompt"
        assert param.description == "Text prompt for generation"
        assert param.type == "string"
        assert param.default == "a beautiful landscape"
        assert param.required is True

    def test_create_int_parameter(self) -> None:
        """Test creating an integer template parameter."""
        param = TemplateParameter(
            name="steps",
            description="Number of sampling steps",
            type="int",
            default=20,
            required=False,
        )

        assert param.name == "steps"
        assert param.type == "int"
        assert param.default == 20
        assert param.required is False

    def test_create_float_parameter(self) -> None:
        """Test creating a float template parameter."""
        param = TemplateParameter(
            name="cfg",
            description="Classifier-free guidance scale",
            type="float",
            default=8.0,
        )

        assert param.type == "float"
        assert param.default == 8.0

    def test_parameter_requires_fields(self) -> None:
        """Test that name, description, and type are required."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateParameter(description="test", type="string")  # type: ignore

        assert "name" in str(exc_info.value)

    def test_parameter_serialization(self) -> None:
        """Test parameter serialization to dict."""
        param = TemplateParameter(
            name="width",
            description="Image width",
            type="int",
            default=512,
        )

        data = param.model_dump()
        assert data == {
            "name": "width",
            "description": "Image width",
            "type": "int",
            "default": 512,
            "required": True,
        }


class TestWorkflowTemplate:
    """Tests for WorkflowTemplate model."""

    def test_create_simple_template(self) -> None:
        """Test creating a simple workflow template."""
        template = WorkflowTemplate(
            name="Simple Template",
            description="A basic template for testing",
            parameters={},
            nodes={},
        )

        assert template.name == "Simple Template"
        assert template.description == "A basic template for testing"
        assert template.parameters == {}
        assert template.nodes == {}

    def test_create_template_with_metadata(self) -> None:
        """Test creating a template with full metadata."""
        template = WorkflowTemplate(
            name="Character Portrait",
            description="Generate character portraits for RPGs",
            category="character",
            parameters={},
            nodes={},
        )

        assert template.name == "Character Portrait"
        assert template.category == "character"

    def test_create_template_with_parameters(self) -> None:
        """Test creating a template with parameter definitions."""
        template = WorkflowTemplate(
            name="Configurable Template",
            description="Template with parameters",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Text prompt",
                    type="string",
                    default="a landscape",
                ),
                "steps": TemplateParameter(
                    name="steps",
                    description="Sampling steps",
                    type="int",
                    default=20,
                ),
            },
            nodes={},
        )

        assert "prompt" in template.parameters
        assert "steps" in template.parameters
        assert template.parameters["prompt"].type == "string"
        assert template.parameters["steps"].default == 20

    def test_create_template_with_workflow_nodes(self) -> None:
        """Test creating a template with workflow nodes."""
        template = WorkflowTemplate(
            name="Complete Template",
            description="Template with nodes",
            parameters={},
            nodes={
                "1": WorkflowNode(
                    class_type="CheckpointLoaderSimple",
                    inputs={"ckpt_name": "model.safetensors"},
                ),
                "2": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": 123, "steps": 20, "model": ["1", 0]},
                ),
            },
        )

        assert "1" in template.nodes
        assert "2" in template.nodes
        assert template.nodes["1"].class_type == "CheckpointLoaderSimple"

    def test_template_requires_name_and_description(self) -> None:
        """Test that name and description are required."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowTemplate(parameters={}, nodes={})  # type: ignore

        error_str = str(exc_info.value)
        assert "name" in error_str or "description" in error_str

    def test_template_serialization(self) -> None:
        """Test template serialization to dict."""
        template = WorkflowTemplate(
            name="Test Template",
            description="For testing",
            category="test",
            parameters={
                "width": TemplateParameter(
                    name="width", description="Width", type="int", default=512
                )
            },
            nodes={"1": WorkflowNode(class_type="Test", inputs={"param": "value"})},
        )

        data = template.model_dump()

        assert data["name"] == "Test Template"
        assert data["category"] == "test"
        assert "width" in data["parameters"]
        assert "1" in data["nodes"]

    def test_instantiate_workflow_from_template(self) -> None:
        """Test creating a WorkflowPrompt instance from template."""
        template = WorkflowTemplate(
            name="Character Generator",
            description="Generate character images",
            parameters={
                "prompt": TemplateParameter(
                    name="prompt",
                    description="Character description",
                    type="string",
                    default="a warrior",
                ),
                "seed": TemplateParameter(
                    name="seed", description="Random seed", type="int", default=123
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode",
                    inputs={"text": "{{prompt}}"},  # Placeholder
                ),
                "2": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": "{{seed}}", "positive": ["1", 0]},  # Placeholders
                ),
            },
        )

        # Instantiate with custom parameters
        workflow = template.instantiate({"prompt": "a mage", "seed": 456})

        assert isinstance(workflow, WorkflowPrompt)
        assert "1" in workflow.nodes
        assert "2" in workflow.nodes
        assert workflow.nodes["1"].inputs["text"] == "a mage"
        assert workflow.nodes["2"].inputs["seed"] == 456

    def test_instantiate_uses_defaults(self) -> None:
        """Test that instantiate uses default parameter values."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={
                "steps": TemplateParameter(
                    name="steps", description="Steps", type="int", default=20
                )
            },
            nodes={
                "1": WorkflowNode(class_type="KSampler", inputs={"steps": "{{steps}}"})
            },
        )

        # Instantiate without providing steps parameter
        workflow = template.instantiate({})

        assert workflow.nodes["1"].inputs["steps"] == 20


class TestGenerationResult:
    """Tests for GenerationResult model."""

    def test_create_simple_result(self) -> None:
        """Test creating a simple generation result."""
        result = GenerationResult(
            images=["output/image1.png"],
            execution_time=5.2,
        )

        assert result.images == ["output/image1.png"]
        assert result.execution_time == 5.2
        assert result.metadata == {}
        assert result.prompt_id is None
        assert result.seed is None

    def test_create_result_with_multiple_images(self) -> None:
        """Test creating a result with multiple generated images."""
        result = GenerationResult(
            images=[
                "output/image1.png",
                "output/image2.png",
                "output/image3.png",
            ],
            execution_time=15.7,
        )

        assert len(result.images) == 3
        assert "output/image1.png" in result.images
        assert "output/image2.png" in result.images
        assert "output/image3.png" in result.images

    def test_create_result_with_metadata(self) -> None:
        """Test creating a result with generation metadata."""
        result = GenerationResult(
            images=["output/character.png"],
            execution_time=8.5,
            metadata={
                "model": "v1-5-pruned-emaonly.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg": 8.0,
                "sampler": "euler",
            },
        )

        assert result.metadata["model"] == "v1-5-pruned-emaonly.safetensors"
        assert result.metadata["width"] == 512
        assert result.metadata["height"] == 768
        assert result.metadata["steps"] == 20

    def test_create_result_with_prompt_id(self) -> None:
        """Test creating a result with ComfyUI prompt ID."""
        result = GenerationResult(
            images=["output/test.png"],
            execution_time=3.2,
            prompt_id="prompt-12345",
        )

        assert result.prompt_id == "prompt-12345"

    def test_create_result_with_seed(self) -> None:
        """Test creating a result with seed value."""
        result = GenerationResult(
            images=["output/test.png"],
            execution_time=4.1,
            seed=987654321,
        )

        assert result.seed == 987654321

    def test_create_result_with_all_fields(self) -> None:
        """Test creating a result with all fields populated."""
        result = GenerationResult(
            images=["output/final.png", "output/final2.png"],
            execution_time=12.3,
            metadata={
                "template": "character-portrait",
                "model": "sdxl-base.safetensors",
                "prompt": "a warrior in armor",
            },
            prompt_id="prompt-abc123",
            seed=42,
        )

        assert len(result.images) == 2
        assert result.execution_time == 12.3
        assert result.metadata["template"] == "character-portrait"
        assert result.prompt_id == "prompt-abc123"
        assert result.seed == 42

    def test_result_requires_images(self) -> None:
        """Test that images field is required."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationResult(execution_time=1.0)  # type: ignore

        assert "images" in str(exc_info.value)

    def test_result_requires_execution_time(self) -> None:
        """Test that execution_time field is required."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationResult(images=["test.png"])  # type: ignore

        assert "execution_time" in str(exc_info.value)

    def test_result_empty_images_list(self) -> None:
        """Test that empty images list is valid (generation with no output)."""
        result = GenerationResult(
            images=[],
            execution_time=2.5,
        )

        assert result.images == []
        assert result.execution_time == 2.5

    def test_result_negative_execution_time(self) -> None:
        """Test that negative execution time is allowed (validation elsewhere)."""
        # Note: We allow negative times at the model level; validation should
        # happen at a higher level if needed
        result = GenerationResult(
            images=["test.png"],
            execution_time=-1.0,
        )

        assert result.execution_time == -1.0

    def test_result_serialization(self) -> None:
        """Test that result can be serialized to dict/JSON."""
        result = GenerationResult(
            images=["output/test.png"],
            execution_time=5.5,
            metadata={"model": "sd-v1-5"},
            prompt_id="test-123",
            seed=999,
        )

        data = result.model_dump()

        assert data["images"] == ["output/test.png"]
        assert data["execution_time"] == 5.5
        assert data["metadata"] == {"model": "sd-v1-5"}
        assert data["prompt_id"] == "test-123"
        assert data["seed"] == 999

    def test_result_from_dict(self) -> None:
        """Test creating result from dictionary."""
        data = {
            "images": ["img1.png", "img2.png"],
            "execution_time": 7.8,
            "metadata": {"steps": 20},
            "prompt_id": "abc",
            "seed": 123,
        }

        result = GenerationResult(**data)  # type: ignore[arg-type]

        assert result.images == ["img1.png", "img2.png"]
        assert result.execution_time == 7.8
        assert result.metadata["steps"] == 20
        assert result.prompt_id == "abc"
        assert result.seed == 123


class TestGenerationRequest:
    """Tests for GenerationRequest model."""

    def test_create_simple_request(self) -> None:
        """Test creating a simple generation request with minimal fields."""
        request = GenerationRequest(
            template_id="character-portrait",
        )

        assert request.template_id == "character-portrait"
        assert request.params == {}
        assert request.output_settings == {}

    def test_create_request_with_params(self) -> None:
        """Test creating a request with template parameters."""
        request = GenerationRequest(
            template_id="character-portrait",
            params={
                "prompt": "a warrior in armor",
                "seed": 42,
                "steps": 20,
            },
        )

        assert request.template_id == "character-portrait"
        assert request.params["prompt"] == "a warrior in armor"
        assert request.params["seed"] == 42
        assert request.params["steps"] == 20

    def test_create_request_with_output_settings(self) -> None:
        """Test creating a request with output settings."""
        request = GenerationRequest(
            template_id="item-icon",
            output_settings={
                "output_dir": "/path/to/output",
                "format": "png",
                "quality": 95,
            },
        )

        assert request.template_id == "item-icon"
        assert request.output_settings["output_dir"] == "/path/to/output"
        assert request.output_settings["format"] == "png"
        assert request.output_settings["quality"] == 95

    def test_create_request_with_all_fields(self) -> None:
        """Test creating a request with all fields populated."""
        request = GenerationRequest(
            template_id="environment-texture",
            params={
                "prompt": "grass texture, seamless",
                "width": 512,
                "height": 512,
                "seed": 999,
            },
            output_settings={
                "output_dir": "/game/assets/textures",
                "format": "png",
                "filename_prefix": "grass_",
            },
        )

        assert request.template_id == "environment-texture"
        assert len(request.params) == 4
        assert request.params["prompt"] == "grass texture, seamless"
        assert request.params["width"] == 512
        assert len(request.output_settings) == 3
        assert request.output_settings["filename_prefix"] == "grass_"

    def test_request_requires_template_id(self) -> None:
        """Test that template_id field is required."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest()  # type: ignore

        assert "template_id" in str(exc_info.value)

    def test_request_params_default_empty_dict(self) -> None:
        """Test that params defaults to empty dict."""
        request = GenerationRequest(template_id="test-template")

        assert request.params == {}
        assert isinstance(request.params, dict)

    def test_request_output_settings_default_empty_dict(self) -> None:
        """Test that output_settings defaults to empty dict."""
        request = GenerationRequest(template_id="test-template")

        assert request.output_settings == {}
        assert isinstance(request.output_settings, dict)

    def test_request_params_various_types(self) -> None:
        """Test that params can contain various value types."""
        request = GenerationRequest(
            template_id="test",
            params={
                "string_param": "value",
                "int_param": 42,
                "float_param": 3.14,
                "bool_param": True,
                "list_param": [1, 2, 3],
                "dict_param": {"nested": "value"},
            },
        )

        assert request.params["string_param"] == "value"
        assert request.params["int_param"] == 42
        assert request.params["float_param"] == 3.14
        assert request.params["bool_param"] is True
        assert request.params["list_param"] == [1, 2, 3]
        assert request.params["dict_param"]["nested"] == "value"

    def test_request_serialization(self) -> None:
        """Test that request can be serialized to dict/JSON."""
        request = GenerationRequest(
            template_id="character-portrait",
            params={"prompt": "a mage", "seed": 123},
            output_settings={"format": "png"},
        )

        data = request.model_dump()

        assert data["template_id"] == "character-portrait"
        assert data["params"] == {"prompt": "a mage", "seed": 123}
        assert data["output_settings"] == {"format": "png"}

    def test_request_from_dict(self) -> None:
        """Test creating request from dictionary."""
        data = {
            "template_id": "item-icon",
            "params": {"prompt": "sword icon", "steps": 30},
            "output_settings": {"output_dir": "/output"},
        }

        request = GenerationRequest(**data)  # type: ignore[arg-type]

        assert request.template_id == "item-icon"
        assert request.params["prompt"] == "sword icon"
        assert request.params["steps"] == 30
        assert request.output_settings["output_dir"] == "/output"

    def test_request_empty_template_id_invalid(self) -> None:
        """Test that empty template_id is invalid."""
        with pytest.raises(ValidationError):
            GenerationRequest(template_id="")

    def test_request_with_workflow_specific_params(self) -> None:
        """Test request with ComfyUI-specific workflow parameters."""
        request = GenerationRequest(
            template_id="advanced-workflow",
            params={
                "positive_prompt": "masterpiece, best quality",
                "negative_prompt": "low quality, blurry",
                "sampler": "euler_a",
                "scheduler": "karras",
                "cfg_scale": 7.5,
                "denoise": 1.0,
            },
        )

        assert request.params["positive_prompt"] == "masterpiece, best quality"
        assert request.params["negative_prompt"] == "low quality, blurry"
        assert request.params["cfg_scale"] == 7.5
        assert request.params["denoise"] == 1.0
