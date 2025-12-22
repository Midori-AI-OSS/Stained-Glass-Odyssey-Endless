"""Tests for the agent loader module."""
import llms.agent_loader
from llms.agent_loader import load_agent
from llms.agent_loader import validate_agent
import pytest


class FakeAgent:
    """Fake agent for testing."""

    async def invoke(self, payload):
        """Fake invoke method."""
        class FakeResponse:
            def __init__(self, text):
                self.response = text

        return FakeResponse(f"Response to: {payload.user_message}")

    async def supports_streaming(self):
        """Fake streaming support check."""
        return False


@pytest.mark.asyncio
async def test_load_agent_requires_framework(monkeypatch):
    """Test that load_agent raises ImportError when framework not available."""

    monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", False)

    with pytest.raises(ImportError, match="Agent framework is not available"):
        await load_agent()


@pytest.mark.asyncio
async def test_load_agent_openai_backend(monkeypatch):
    """Test loading agent with OpenAI backend."""

    monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", True)
    monkeypatch.setenv("OPENAI_API_URL", "https://test.api.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    called = {}

    async def fake_get_agent(**kwargs):
        called.update(kwargs)
        return FakeAgent()

    monkeypatch.setattr(llms.agent_loader, "get_agent", fake_get_agent)

    agent = await load_agent(validate=False)

    assert agent is not None
    assert called["backend"] == "openai"
    assert called["api_key"] == "test-key"
    assert called["base_url"] == "https://test.api.com/v1"


@pytest.mark.asyncio
async def test_load_agent_huggingface_backend(monkeypatch):
    """Test loading agent with HuggingFace backend."""

    monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", True)
    monkeypatch.setenv("OPENAI_API_URL", "unset")
    # Need to monkeypatch the imported is_torch_available in agent_loader module
    monkeypatch.setattr(llms.agent_loader, "is_torch_available", lambda: True)

    called = {}

    async def fake_get_agent(**kwargs):
        called.update(kwargs)
        return FakeAgent()

    monkeypatch.setattr(llms.agent_loader, "get_agent", fake_get_agent)

    agent = await load_agent(validate=False)

    assert agent is not None
    assert called["backend"] == "huggingface"
    assert called["model"] == "openai/gpt-oss-20b"  # Default model


@pytest.mark.asyncio
async def test_load_agent_no_backend_available(monkeypatch):
    """Test that load_agent raises ValueError when no backend available."""
    import llms.torch_checker

    monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", True)
    monkeypatch.setenv("OPENAI_API_URL", "unset")
    monkeypatch.setattr(llms.torch_checker, "is_torch_available", lambda: False)

    with pytest.raises(ValueError, match="No backend available"):
        await load_agent()


@pytest.mark.asyncio
async def test_validate_agent_success(monkeypatch):
    """Test agent validation success."""

    monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", True)

    # Mock AgentPayload
    class MockAgentPayload:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    # Create a mock module for midori_ai_agent_base
    import sys
    import types

    mock_module = types.ModuleType("midori_ai_agent_base")
    mock_module.AgentPayload = MockAgentPayload
    sys.modules["midori_ai_agent_base"] = mock_module

    agent = FakeAgent()
    is_valid = await validate_agent(agent)

    assert is_valid is True

    # Clean up
    del sys.modules["midori_ai_agent_base"]


@pytest.mark.asyncio
async def test_validate_agent_short_response(monkeypatch):
    """Test agent validation fails with short response."""

    monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", True)

    # Mock AgentPayload
    class MockAgentPayload:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    # Create a mock module for midori_ai_agent_base
    import sys
    import types

    mock_module = types.ModuleType("midori_ai_agent_base")
    mock_module.AgentPayload = MockAgentPayload
    sys.modules["midori_ai_agent_base"] = mock_module

    class ShortResponseAgent:
        async def invoke(self, payload):
            class FakeResponse:
                def __init__(self):
                    self.response = "hi"

            return FakeResponse()

    agent = ShortResponseAgent()
    is_valid = await validate_agent(agent)

    assert is_valid is False

    # Clean up
    del sys.modules["midori_ai_agent_base"]


@pytest.mark.asyncio
async def test_validate_agent_error(monkeypatch):
    """Test agent validation handles errors."""

    monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", True)

    # Mock AgentPayload
    class MockAgentPayload:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    # Create a mock module for midori_ai_agent_base
    import sys
    import types

    mock_module = types.ModuleType("midori_ai_agent_base")
    mock_module.AgentPayload = MockAgentPayload
    sys.modules["midori_ai_agent_base"] = mock_module

    class ErrorAgent:
        async def invoke(self, payload):
            raise RuntimeError("Test error")

    agent = ErrorAgent()
    is_valid = await validate_agent(agent)

    assert is_valid is False

    # Clean up
    del sys.modules["midori_ai_agent_base"]
