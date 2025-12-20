"""Test agent loader dependencies."""
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))


@pytest.mark.asyncio
async def test_agent_loader_without_framework() -> None:
    """Test that agent loader raises ImportError when framework not available."""
    from unittest.mock import patch

    # Mock the agent framework as not available
    with patch("llms.agent_loader._AGENT_FRAMEWORK_AVAILABLE", False):
        from llms import load_agent

        # This should raise ImportError about agent framework
        with pytest.raises(ImportError, match="Agent framework is not available"):
            await load_agent()


@pytest.mark.asyncio
async def test_agent_loader_with_framework_available() -> None:
    """Test that agent loader works when framework is available."""
    from unittest.mock import AsyncMock
    from unittest.mock import MagicMock
    from unittest.mock import patch

    mock_agent = MagicMock()
    mock_get_agent = AsyncMock(return_value=mock_agent)

    with patch("llms.agent_loader._AGENT_FRAMEWORK_AVAILABLE", True):
        with patch("llms.agent_loader.get_agent", mock_get_agent):
            from llms import load_agent

            # This should work with framework available
            agent = await load_agent(model="test-model")
            assert agent is not None
            assert agent == mock_agent
