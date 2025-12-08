from __future__ import annotations

from pathlib import Path

from options import set_option
import pytest

from autofighter.party import Party
from autofighter.rooms.chat import ChatRoom
from autofighter.stats import Stats


class FakeAgent:
    """Fake agent that mimics the agent framework interface."""

    def __init__(self, calls: dict[str, str]) -> None:
        self._calls = calls

    async def invoke(self, payload):
        """Fake invoke method."""
        self._calls["model"] = getattr(self, "_model", "unknown")
        self._calls["user_message"] = payload.user_message
        self._calls["system_context"] = payload.system_context

        class FakeResponse:
            def __init__(self):
                self.response = "reply"

        return FakeResponse()

    async def supports_streaming(self):
        """Fake streaming support check."""
        return False


@pytest.fixture()
def setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "k")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    set_option("lrm_model", "gemma:2b")
    return db_path


@pytest.mark.asyncio
async def test_chat_room_uses_selected_model(monkeypatch, setup_db):
    import sys
    import types

    # Mock the midori_ai_agent_base module
    mock_module = types.ModuleType("midori_ai_agent_base")

    class MockAgentPayload:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    mock_module.AgentPayload = MockAgentPayload
    sys.modules["midori_ai_agent_base"] = mock_module

    calls: dict[str, str] = {}

    async def fake_loader(backend=None, model=None):
        agent = FakeAgent(calls)
        agent._model = model
        calls["model"] = model
        calls["backend"] = backend
        return agent

    monkeypatch.setattr("autofighter.rooms.chat.load_agent", fake_loader)

    # Create a member with character attributes
    member = Stats()
    member.id = "test_member"
    member.instance_id = "test_member"
    member.name = "TestChar"
    member.summarized_about = "A test character"
    member.looks = "A generic appearance"
    party = Party(members=[member])

    # Create a simple mock node
    from autofighter.mapgen import MapNode
    node = MapNode(room_id=1, room_type="chat", floor=1, index=0, loop=0, pressure=0)

    room = ChatRoom(node=node)
    result = await room.resolve(party, {"message": "hi"})

    # Response should include character name
    assert "TestChar:" in result["response"]
    assert "reply" in result["response"]
    assert "hi" in calls["user_message"]
    assert calls["model"] == "gemma:2b"
    # Verify system context includes character info
    assert "You are TestChar" in calls["system_context"]
    assert "A test character" in calls["system_context"]

    # Clean up
    del sys.modules["midori_ai_agent_base"]
