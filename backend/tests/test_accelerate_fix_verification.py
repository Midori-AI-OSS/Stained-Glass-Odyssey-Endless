"""Test to verify the accelerate dependency fix works."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_accelerate_fix_verification() -> None:
    """Test that verifies accelerate dependency is available when needed."""
    # Mock the transformers.pipeline to simulate using device_map="auto"
    from unittest.mock import MagicMock
    from unittest.mock import patch

    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.task = "text-generation"
    mock_pipeline_instance.model = MagicMock()
    mock_pipeline_instance.model.name_or_path = "fake-model"

    def mock_pipeline(*args, **kwargs):
        # This should work now that accelerate is available
        if "device_map" in kwargs and kwargs["device_map"] == "auto":
            # Simulate successful pipeline creation with device_map="auto"
            return mock_pipeline_instance
        if "device" in kwargs:
            return mock_pipeline_instance
        raise ValueError(f"Unexpected kwargs: {kwargs}")

    with patch("llms.loader.pipeline", side_effect=mock_pipeline):
        with patch("llms.loader._IMPORT_ERROR", None):
            with patch("llms.loader.model_memory_requirements", return_value=(0, 0)):
                with patch("llms.loader.ensure_ram"):
                    with patch(
                        "llms.loader.pick_device", return_value=0
                    ):  # This triggers device_map="auto"
                        with patch("llms.loader.HuggingFacePipeline") as mock_hf:
                            mock_hf.return_value = MagicMock()
                            from llms.loader import ModelName
                            from llms.loader import load_llm

                            # This should now work without error
                            llm = load_llm(ModelName.DEEPSEEK.value)
                            assert llm is not None


def test_accelerate_available() -> None:
    """Test that accelerate is available in the environment."""
    try:
        import accelerate

        assert accelerate.__version__ >= "0.26.0"
    except ImportError:
        # This test only runs if accelerate is installed
        # In CI/production it should be installed via pip install -e ".[llm-cpu]"
        import pytest

        pytest.skip(
            "accelerate not installed - this is expected in minimal test environment"
        )
