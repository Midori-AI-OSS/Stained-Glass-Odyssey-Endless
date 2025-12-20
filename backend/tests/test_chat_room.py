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
    calls: dict[str, str] = {}

    async def fake_loader(model: str = None, **kwargs):
        calls["model"] = model
        return FakeAgent(calls)

    monkeypatch.setattr("autofighter.rooms.chat.load_agent", fake_loader)
    member = Stats()
    party = Party(members=[member])
    room = ChatRoom()
    result = await room.resolve(party, {"message": "hi"})
    assert result["response"] == "reply"
    assert "hi" in calls["prompt"]
    assert calls["model"] == "google/gemma-3-4b-it"
