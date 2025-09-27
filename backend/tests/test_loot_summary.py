import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
import autofighter.rooms.battle.core as rooms_module
from autofighter.stats import Stats
from plugins.damage_types import ALL_DAMAGE_TYPES


@pytest.fixture(autouse=True)
def stub_battle_flow(monkeypatch):
    """Replace heavy battle dependencies with lightweight stubs for tests."""

    upgrade_ids = sorted({entry.lower() for entry in ALL_DAMAGE_TYPES})
    upgrade_id = upgrade_ids[0] if upgrade_ids else "physical"

    async def fake_setup_battle(*_args, **_kwargs):
        return object()

    async def fake_enrage_threshold(*_args, **_kwargs):
        return 42

    async def fake_run_battle(
        room,
        *,
        party,
        setup_data,
        start_gold,
        enrage_threshold,
        progress,
        run_id,
        battle_snapshots,
        battle_tasks,
    ):
        del party, setup_data, enrage_threshold, progress, run_id, battle_snapshots, battle_tasks

        is_boss = str(getattr(room.node, "room_type", "")).startswith("battle-boss")
        star_value = 4 if is_boss else 2
        return {
            "result": "victory",
            "loot": {
                "gold": start_gold + 100,
                "card_choices": [],
                "relic_choices": [],
                "items": [
                    {"id": upgrade_id, "stars": star_value},
                    {"id": "ticket", "stars": 0},
                ],
            },
        }

    monkeypatch.setattr(rooms_module, "setup_battle", fake_setup_battle)
    monkeypatch.setattr(rooms_module, "compute_enrage_threshold", fake_enrage_threshold)
    monkeypatch.setattr(rooms_module, "run_battle", fake_run_battle)
    monkeypatch.setattr(rooms_module, "card_choices", lambda *_args, **_kwargs: [])


@pytest.mark.asyncio
async def test_battle_returns_loot_summary():
    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    party = Party(members=[member])

    result = await room.resolve(party, {})

    assert "loot" in result
    loot = result["loot"]
    assert set(loot).issuperset({"gold", "card_choices", "relic_choices", "items"})
    assert loot["gold"] > 0
    upgrades = [item for item in loot["items"] if item["id"] != "ticket"]
    assert upgrades
    valid_ids = {entry.lower() for entry in ALL_DAMAGE_TYPES}
    for item in upgrades:
        assert item["id"] in valid_ids
        assert 1 <= item["stars"] <= 4


@pytest.mark.asyncio
async def test_floor_boss_high_star_items():
    node = MapNode(room_id=1, room_type="battle-boss-floor", floor=1, index=1, loop=1, pressure=0)
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    party = Party(members=[member])

    result = await room.resolve(party, {})
    stars = [item["stars"] for item in result["loot"]["items"] if item["id"] != "ticket"]
    assert stars and stars[0] >= 3
