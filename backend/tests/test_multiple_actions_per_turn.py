import pytest

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from autofighter.stats import BUS
from plugins.foes._base import FoeBase
from plugins.players import player as player_mod


class DummyFoe(FoeBase):
    id = "dummy"
    name = "Dummy"


@pytest.mark.asyncio
async def test_swift_footwork_multiple_actions_and_queue(monkeypatch):
    node = MapNode(room_id=0, room_type="battle", floor=1, index=1, loop=1, pressure=0)
    room = BattleRoom(node)
    player = player_mod.Player()
    player.set_base_stat("atk", 50)
    party = Party(members=[player])
    award_card(party, "swift_footwork")
    await apply_cards(party)

    foe = DummyFoe()
    foe.hp = 1000
    monkeypatch.setattr("autofighter.rooms.utils._choose_foe", lambda p: foe)
    monkeypatch.setattr("autofighter.rooms.utils._scale_stats", lambda *args, **kwargs: None)

    snapshots: list[dict] = []
    async def collector(snap):
        snapshots.append(snap)

    actions: list[int] = []
    def _count(actor, *_):
        if actor.id == player.id:
            actions.append(1)
    BUS.subscribe("action_used", _count)

    await room.resolve(party, {}, progress=collector)
    BUS.unsubscribe("action_used", _count)

    # Player should act three times (two from card and one free opener)
    assert len(actions) == 3

    # Initial snapshot queue should show two upcoming turns for player (extra action)
    queue = [q for q in snapshots[0]["action_queue"] if q["id"] == player.id]
    assert len(queue) == 2
    assert any(q.get("bonus") for q in queue)
