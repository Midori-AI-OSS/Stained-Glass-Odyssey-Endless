"""Test to reproduce the accelerate dependency issue."""

from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from llms.loader import ModelName


def test_accelerate_missing_error() -> None:
    """Test that reproduces the accelerate dependency error."""
    # This test demonstrates the issue when accelerate is not installed
    # and device_map="auto" is used
    from unittest.mock import patch

    # Mock transformers.pipeline to raise the actual accelerate error
    def mock_pipeline(*args, **kwargs):
        if "device_map" in kwargs and kwargs["device_map"] == "auto":
            raise ImportError(
                "Using `low_cpu_mem_usage=True` or a `device_map` requires Accelerate: `pip install 'accelerate>=0.26.0'`"
            )
        return None

    with patch("llms.loader.pipeline", side_effect=mock_pipeline):
        with patch("llms.loader._IMPORT_ERROR", None):
            with patch("llms.loader.model_memory_requirements", return_value=(0, 0)):
                with patch("llms.loader.ensure_ram"):
                    with patch(
                        "llms.loader.pick_device", return_value=0
                    ):  # This triggers device_map="auto"
                        from llms.loader import load_llm

                        # This should raise the ImportError about accelerate
                        with pytest.raises(ImportError, match="Accelerate"):
                            load_llm(ModelName.DEEPSEEK.value)


def test_accelerate_not_needed_with_explicit_device() -> None:
    """Test that accelerate is not needed when using explicit device."""
    from unittest.mock import MagicMock
    from unittest.mock import patch

    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.task = "text-generation"
    mock_pipeline_instance.model = MagicMock()
    mock_pipeline_instance.model.name_or_path = "fake"

    def mock_pipeline(*args, **kwargs):
        # Should not raise error when device is explicit (not device_map="auto")
        if "device" in kwargs and kwargs["device"] == -1:
            return mock_pipeline_instance
        raise ValueError("Unexpected kwargs")

    with patch("llms.loader.pipeline", side_effect=mock_pipeline):
        with patch("llms.loader._IMPORT_ERROR", None):
            with patch("llms.loader.model_memory_requirements", return_value=(0, 0)):
                with patch("llms.loader.ensure_ram"):
                    with patch(
                        "llms.loader.pick_device", return_value=-1
                    ):  # This triggers device=-1
                        with patch("llms.loader.HuggingFacePipeline") as mock_hf:
                            mock_hf.return_value = MagicMock()
                            from llms.loader import load_llm

                            # This should work without accelerate
                            llm = load_llm(ModelName.DEEPSEEK.value)
                            assert llm is not None
