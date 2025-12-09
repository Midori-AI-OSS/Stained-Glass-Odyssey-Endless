from __future__ import annotations

from pathlib import Path

from llms.loader import ModelName
from options import set_option
import pytest

from autofighter.party import Party
from autofighter.rooms.chat import ChatRoom
from autofighter.stats import Stats


class FakeLLM:
    def __init__(self, calls: dict[str, str]) -> None:
        self._calls = calls

    async def generate_stream(self, text: str):
        self._calls["prompt"] = text
        yield "reply"


@pytest.fixture()
def setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "k")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    set_option("lrm_model", ModelName.GEMMA.value)
    return db_path


@pytest.mark.asyncio
async def test_chat_room_uses_selected_model(monkeypatch, setup_db):
    calls: dict[str, str] = {}

    def fake_loader(model: str):
        calls["model"] = model
        return FakeLLM(calls)

    monkeypatch.setattr("autofighter.rooms.chat.load_llm", fake_loader)
    member = Stats()
    party = Party(members=[member])
    room = ChatRoom()
    result = await room.resolve(party, {"message": "hi"})
    assert result["response"] == "reply"
    assert "hi" in calls["prompt"]
    assert calls["model"] == ModelName.GEMMA.value
