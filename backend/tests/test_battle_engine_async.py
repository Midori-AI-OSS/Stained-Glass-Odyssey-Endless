import itertools
from types import SimpleNamespace

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
import autofighter.rooms.battle.engine as engine
from autofighter.stats import Stats
from plugins.characters.player import Player


@pytest.mark.asyncio
async def test_run_battle_uses_async_gold_event(monkeypatch):
    node = MapNode(room_id=0, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    party = Party(members=[Player()])
    foe = Stats()
    foe.id = "dummy-foe"
    foe.level = 1
    foe.hp = 1
    foe._base_max_hp = 1
    foe._base_atk = 0
    foe._base_defense = 0

    player = party.members[0]
    player._base_atk = 5

    events: list[str] = []
    sleeps: list[float] = []
    batched_events: list[str] = []

    original_emit_async = engine.BUS.emit_async

    async def tracking_emit(event: str, *args):
        if event == "gold_earned":
            events.append(event)
        return await original_emit_async(event, *args)

    monkeypatch.setattr(engine.BUS, "emit_async", tracking_emit)

    original_emit_batched = engine.BUS.emit_batched

    def tracking_emit_batched(event: str, *args):
        batched_events.append(event)
        return original_emit_batched(event, *args)

    monkeypatch.setattr(engine.BUS, "emit_batched", tracking_emit_batched)

    async def fast_sleep(duration: float) -> None:
        sleeps.append(duration)

    monkeypatch.setattr(engine.asyncio, "sleep", fast_sleep)

    monkeypatch.setattr(engine, "get_user_level", lambda: 1)

    async def fake_gain(amount: int) -> dict[str, int]:
        return {"level": 1, "exp": amount, "next_level_exp": 100}

    monkeypatch.setattr(engine, "gain_user_exp", fake_gain)
    monkeypatch.setattr(engine, "end_battle_logging", lambda result: None)
    monkeypatch.setattr(engine, "_calc_gold", lambda room, rdr: 5)
    monkeypatch.setattr(engine, "_pick_card_stars", lambda room: 1)
    monkeypatch.setattr(engine, "_pick_item_stars", lambda room: 1)
    monkeypatch.setattr(engine, "_roll_relic_drop", lambda room, rdr: False)

    card_counter = itertools.count()

    def fake_card_choices(combat_party, stars, count=1):
        idx = next(card_counter)
        return [
            SimpleNamespace(
                id=f"card_{idx}",
                name=f"Card {idx}",
                stars=stars,
                about="test",
            )
        ]

    monkeypatch.setattr(engine, "card_choices", fake_card_choices)

    room = BattleRoom(node=node)
    result = await room.resolve(party, {}, foe=foe)

    assert result["loot"]["gold"] == 5
    assert "gold_earned" in events
    assert "gold_earned" not in batched_events
    assert any(sleeps)
