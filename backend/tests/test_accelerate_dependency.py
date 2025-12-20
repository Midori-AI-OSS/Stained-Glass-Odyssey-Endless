"""Test agent loader dependencies."""
from pathlib import Path
import sys
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))


@pytest.mark.asyncio
async def test_agent_loader_without_framework() -> None:
    """Test that agent loader raises ImportError when framework not available."""
    from llms.agent_loader import load_agent

    # Mock the agent framework as not available by patching the check
    with patch("llms.agent_loader._AGENT_FRAMEWORK_AVAILABLE", False):
        # This should raise ImportError about agent framework
        with pytest.raises(ImportError, match="Agent framework is not available"):
            await load_agent()


@pytest.mark.asyncio
async def test_agent_loader_with_framework_available() -> None:
    """Test that agent loader works when framework is available."""
    from llms.agent_loader import load_agent

    mock_agent = MagicMock()
    mock_get_agent = AsyncMock(return_value=mock_agent)

    # Mock both the availability check and the get_agent function
    with patch("llms.agent_loader._AGENT_FRAMEWORK_AVAILABLE", True):
        with patch("llms.agent_loader.get_agent", mock_get_agent):
            with patch("llms.agent_loader.find_config_file", return_value=None):
                # This should work with framework available
                # Pass use_config=False and backend explicitly to bypass auto-detection
                agent = await load_agent(backend="openai", model="test-model", use_config=False)
                assert agent is not None
                assert agent == mock_agent

                # Verify get_agent was called with expected parameters
                mock_get_agent.assert_called_once()
