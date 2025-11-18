"""Tests for comfyui_mcp.models module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from comfyui_mcp.models import WorkflowNode, WorkflowPrompt


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

        prompt = WorkflowPrompt(**data)

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
