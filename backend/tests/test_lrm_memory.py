import pytest

from plugins.characters.foe_base import FoeBase
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_player_memory_isolated() -> None:
    p1 = PlayerBase()
    p1.run_id = "run"
    p2 = PlayerBase()
    p2.run_id = "run"
    await p1.send_lrm_message("hi")
    await p2.send_lrm_message("bye")
    await p1.receive_lrm_message("ok")
    await p2.receive_lrm_message("fine")
    h1 = p1.lrm_memory.load_memory_variables({})["history"]
    h2 = p2.lrm_memory.load_memory_variables({})["history"]
    assert "hi" in h1 and "bye" not in h1 and "ok" in h1
    assert "bye" in h2 and "hi" not in h2 and "fine" in h2


@pytest.mark.asyncio
async def test_foe_memory_isolated() -> None:
    f1 = FoeBase()
    f1.run_id = "run"
    f2 = FoeBase()
    f2.run_id = "run"
    await f1.send_lrm_message("growl")
    await f2.send_lrm_message("snarl")
    await f1.receive_lrm_message("roar")
    await f2.receive_lrm_message("hiss")
    h1 = f1.lrm_memory.load_memory_variables({})["history"]
    h2 = f2.lrm_memory.load_memory_variables({})["history"]
    assert "growl" in h1 and "snarl" not in h1 and "roar" in h1
    assert "snarl" in h2 and "growl" not in h2 and "hiss" in h2
