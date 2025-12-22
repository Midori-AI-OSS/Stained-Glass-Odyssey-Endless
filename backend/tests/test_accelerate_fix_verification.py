"""Test to verify agent framework is properly configured."""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_agent_framework_available() -> None:
    """Test that agent framework is available in the environment."""
    try:
        import midori_ai_agent_base
        import midori_ai_logger
        assert midori_ai_agent_base is not None
        assert midori_ai_logger is not None
    except ImportError:
        # This test only runs if agent framework is installed
        # In CI/production it should be installed via uv sync --extra llm-cpu
        import pytest
        pytest.skip("agent framework not installed - this is expected in minimal test environment")


def test_accelerate_available() -> None:
    """Test that accelerate is available in the environment."""
    try:
        import accelerate
        assert accelerate.__version__ >= "0.26.0"
    except ImportError:
        # This test only runs if accelerate is installed
        # In CI/production it should be installed via uv sync --extra llm-cpu
        import pytest
        pytest.skip("accelerate not installed - this is expected in minimal test environment")
