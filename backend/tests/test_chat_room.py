from __future__ import annotations

from pathlib import Path

from options import set_option
import pytest

from autofighter.party import Party
from autofighter.rooms.chat import ChatRoom
from autofighter.stats import Stats


class FakeAgent:
    def __init__(self, calls: dict[str, str]) -> None:
        self._calls = calls

    async def stream(self, payload):
        self._calls["prompt"] = payload.user_message if hasattr(payload, 'user_message') else str(payload)
        yield "reply"


@pytest.fixture()
def setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "k")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    set_option("lrm_model", "google/gemma-3-4b-it")
    return db_path


@pytest.mark.asyncio
async def test_chat_room_uses_selected_model(monkeypatch, setup_db):
    from autofighter.mapgen import MapNode

    calls: dict[str, str] = {}

    async def fake_loader(model: str = None, **kwargs):
        calls["model"] = model
        return FakeAgent(calls)

    # Mock the AgentPayload class that ChatRoom tries to import
    class MockAgentPayload:
        def __init__(self, user_message, thinking_blob, system_context, user_profile, tools_available, session_id):
            self.user_message = user_message
            self.thinking_blob = thinking_blob
            self.system_context = system_context
            self.user_profile = user_profile
            self.tools_available = tools_available
            self.session_id = session_id

    # Mock the entire midori_ai_agent_base module
    import sys
    from unittest.mock import MagicMock
    mock_module = MagicMock()
    mock_module.AgentPayload = MockAgentPayload
    sys.modules['midori_ai_agent_base'] = mock_module

    monkeypatch.setattr("autofighter.rooms.chat.load_agent", fake_loader)
    member = Stats()
    # Add required fields for serialization
    member.id = "test_member"
    member.name = "Test Member"
    member.instance_id = "test_member_001"
    party = Party(members=[member])
    # Create a minimal MapNode for the ChatRoom
    node = MapNode(room_id=1, room_type="chat", floor=1, index=0, loop=0, pressure=0)
    room = ChatRoom(node=node)
    result = await room.resolve(party, {"message": "hi"})
    assert result["response"] == "reply"
    assert "hi" in calls["prompt"]
    assert calls["model"] == "google/gemma-3-4b-it"
