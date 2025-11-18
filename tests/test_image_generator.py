"""Tests for ImageGenerator workflow orchestration.

Tests the image generation orchestration system including:
- Template loading and instantiation
- Workflow submission to ComfyUI
- Generation result retrieval
- Error handling
- Async execution patterns
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from comfyui_mcp import (
    ComfyUIClient,
    ComfyUIConfig,
    GenerationResult,
    WorkflowNode,
    WorkflowTemplate,
    WorkflowTemplateManager,
)
from comfyui_mcp.exceptions import ComfyUIError
from comfyui_mcp.image_generator import ImageGenerator
from comfyui_mcp.models import TemplateParameter


class TestImageGeneratorInitialization:
    """Tests for ImageGenerator initialization."""

    def test_create_generator_with_client_and_manager(self, tmp_path: Path) -> None:
        """Test creating ImageGenerator with client and template manager."""
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)
        manager = WorkflowTemplateManager(tmp_path)

        generator = ImageGenerator(client=client, template_manager=manager)

        assert generator.client == client
        assert generator.template_manager == manager

    def test_create_generator_with_only_client(self) -> None:
        """Test creating ImageGenerator with only client (no template manager)."""
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)

        generator = ImageGenerator(client=client)

        assert generator.client == client
        assert generator.template_manager is None


class TestImageGeneratorGeneration:
    """Tests for image generation from templates."""

    @pytest.mark.asyncio
    async def test_generate_from_template_success(self, tmp_path: Path) -> None:
        """Test successful image generation from template."""
        # Create template
        template = WorkflowTemplate(
            name="Test Template",
            description="Test template",
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
        template.to_file(tmp_path / "test.json")

        # Setup mocks
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)
        manager = WorkflowTemplateManager(tmp_path)

        # Mock client methods using setattr
        submit_mock = AsyncMock(return_value={"prompt_id": "test-prompt-123"})
        history_mock = AsyncMock(
            return_value=GenerationResult(
                prompt_id="test-prompt-123",
                images=["output_image.png"],
                metadata={"completed": True},
                execution_time=2.5,
            )
        )
        client.submit_workflow = submit_mock  # type: ignore[method-assign]
        client.get_history = history_mock  # type: ignore[method-assign]

        generator = ImageGenerator(client=client, template_manager=manager)

        # Generate image
        result = await generator.generate_from_template(
            template_id="test", parameters={"prompt": "a wizard"}
        )

        assert result.prompt_id == "test-prompt-123"
        assert result.images == ["output_image.png"]
        assert result.metadata["completed"] is True
        assert result.execution_time == 2.5

        # Verify client methods were called
        submit_mock.assert_called_once()
        history_mock.assert_called_once_with("test-prompt-123")

    @pytest.mark.asyncio
    async def test_generate_from_template_missing_template(
        self, tmp_path: Path
    ) -> None:
        """Test generation fails when template not found."""
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)
        manager = WorkflowTemplateManager(tmp_path)

        generator = ImageGenerator(client=client, template_manager=manager)

        with pytest.raises(FileNotFoundError, match="Template not found"):
            await generator.generate_from_template(
                template_id="nonexistent", parameters={}
            )

    @pytest.mark.asyncio
    async def test_generate_from_template_no_template_manager(self) -> None:
        """Test generation fails when no template manager configured."""
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)

        generator = ImageGenerator(client=client)

        with pytest.raises(ValueError, match="template_manager"):
            await generator.generate_from_template(template_id="test", parameters={})

    @pytest.mark.asyncio
    async def test_generate_from_template_submission_fails(
        self, tmp_path: Path
    ) -> None:
        """Test handling of workflow submission failure."""
        # Create template
        template = WorkflowTemplate(
            name="Test Template",
            description="Test template",
            parameters={},
            nodes={"1": WorkflowNode(class_type="Test", inputs={})},
        )
        template.to_file(tmp_path / "test.json")

        # Setup mocks
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)
        manager = WorkflowTemplateManager(tmp_path)

        # Mock submission failure
        submit_mock = AsyncMock(side_effect=ComfyUIError("Submission failed"))
        client.submit_workflow = submit_mock  # type: ignore[method-assign]

        generator = ImageGenerator(client=client, template_manager=manager)

        with pytest.raises(ComfyUIError, match="Submission failed"):
            await generator.generate_from_template(template_id="test", parameters={})


class TestImageGeneratorDirectWorkflow:
    """Tests for image generation from direct WorkflowPrompt."""

    @pytest.mark.asyncio
    async def test_generate_from_workflow_success(self) -> None:
        """Test successful generation from direct workflow prompt."""
        # Setup mocks
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)

        submit_mock = AsyncMock(return_value={"prompt_id": "test-prompt-456"})
        history_mock = AsyncMock(
            return_value=GenerationResult(
                prompt_id="test-prompt-456",
                images=["direct_output.png"],
                metadata={},
                execution_time=1.5,
            )
        )
        client.submit_workflow = submit_mock  # type: ignore[method-assign]
        client.get_history = history_mock  # type: ignore[method-assign]

        generator = ImageGenerator(client=client)

        # Create workflow from template
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={},
            nodes={"1": WorkflowNode(class_type="Test", inputs={})},
        )
        workflow = template.instantiate({})

        # Generate
        result = await generator.generate(workflow=workflow)

        assert result.prompt_id == "test-prompt-456"
        assert result.images == ["direct_output.png"]

        submit_mock.assert_called_once_with(workflow)
        history_mock.assert_called_once_with("test-prompt-456")


class TestImageGeneratorErrorHandling:
    """Tests for error handling in ImageGenerator."""

    @pytest.mark.asyncio
    async def test_generate_handles_history_retrieval_failure(
        self, tmp_path: Path
    ) -> None:
        """Test handling of failure when retrieving generation history."""
        template = WorkflowTemplate(
            name="Test",
            description="Test template",
            parameters={},
            nodes={"1": WorkflowNode(class_type="Test", inputs={})},
        )
        template.to_file(tmp_path / "test.json")

        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)
        manager = WorkflowTemplateManager(tmp_path)

        # Mock successful submission but failed history retrieval
        submit_mock = AsyncMock(return_value={"prompt_id": "test-prompt-789"})
        history_mock = AsyncMock(side_effect=ComfyUIError("History failed"))
        client.submit_workflow = submit_mock  # type: ignore[method-assign]
        client.get_history = history_mock  # type: ignore[method-assign]

        generator = ImageGenerator(client=client, template_manager=manager)

        with pytest.raises(ComfyUIError, match="History failed"):
            await generator.generate_from_template(template_id="test", parameters={})


class TestImageGeneratorIntegration:
    """Integration tests for ImageGenerator."""

    @pytest.mark.asyncio
    async def test_end_to_end_generation_workflow(self, tmp_path: Path) -> None:
        """Test complete end-to-end generation workflow."""
        # Create template with parameters
        template = WorkflowTemplate(
            name="Character Portrait",
            description="Generate character portraits",
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
                    default=42,
                    required=False,
                ),
            },
            nodes={
                "1": WorkflowNode(
                    class_type="CLIPTextEncode", inputs={"text": "{{prompt}}"}
                ),
                "2": WorkflowNode(
                    class_type="KSampler",
                    inputs={"seed": "{{seed}}", "steps": 20},
                ),
            },
        )
        template.to_file(tmp_path / "character-portrait.json")

        # Setup
        config = ComfyUIConfig(url="http://localhost:8188")
        client = ComfyUIClient(config)
        manager = WorkflowTemplateManager(tmp_path)

        # Mock full workflow
        submit_mock = AsyncMock(return_value={"prompt_id": "end-to-end-123"})
        history_mock = AsyncMock(
            return_value=GenerationResult(
                prompt_id="end-to-end-123",
                images=["warrior_portrait.png"],
                metadata={"seed": 42, "steps": 20},
                execution_time=3.2,
            )
        )
        client.submit_workflow = submit_mock  # type: ignore[method-assign]
        client.get_history = history_mock  # type: ignore[method-assign]

        generator = ImageGenerator(client=client, template_manager=manager)

        # Execute
        result = await generator.generate_from_template(
            template_id="character-portrait",
            parameters={"prompt": "a mighty warrior", "seed": 12345},
        )

        # Verify
        assert result.prompt_id == "end-to-end-123"
        assert result.images == ["warrior_portrait.png"]
        assert result.execution_time == 3.2

        # Verify workflow was instantiated correctly
        submit_call = submit_mock.call_args
        submitted_workflow = submit_call[0][0]
        assert submitted_workflow.nodes["1"].inputs["text"] == "a mighty warrior"
        assert submitted_workflow.nodes["2"].inputs["seed"] == 12345
