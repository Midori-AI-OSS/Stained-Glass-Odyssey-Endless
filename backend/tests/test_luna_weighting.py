from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import foe_factory
from autofighter.rooms import utils
from autofighter.rooms.battle import setup as battle_setup
from plugins.players import Player
from plugins.players.luna import Luna


def _capture_weights(monkeypatch, node: MapNode, party: Party) -> dict[str, float]:
    captured: dict[str, float] = {}

    def fake_choices(candidates, weights, k):
        for cls, weight in zip(candidates, weights):
            ident = getattr(cls, "id", getattr(cls, "__name__", ""))
            captured[str(ident)] = weight
        return [candidates[0]]

    monkeypatch.setattr(foe_factory.random, "choices", fake_choices)
    utils._choose_foe(node, party)
    return captured


def test_luna_boss_weight_multiplier_third_floor(monkeypatch) -> None:
    node = MapNode(room_id=0, room_type="boss", floor=3, index=1, loop=1, pressure=0)
    party = Party(members=[Player()])
    weights = _capture_weights(monkeypatch, node, party)
    assert "luna" in weights
    assert weights["luna"] == pytest.approx(6.0)
    others = [value for ident, value in weights.items() if ident != "luna"]
    if others:
        assert weights["luna"] >= max(others)


def test_luna_boss_weight_multiplier_glitched_floor(monkeypatch) -> None:
    node = MapNode(
        room_id=0,
        room_type="boss glitched",
        floor=6,
        index=1,
        loop=1,
        pressure=0,
    )
    party = Party(members=[Player()])
    weights = _capture_weights(monkeypatch, node, party)
    assert weights.get("luna") == pytest.approx(6.0)


def test_luna_boss_weight_default_other_floors(monkeypatch) -> None:
    node = MapNode(room_id=0, room_type="boss", floor=2, index=1, loop=1, pressure=0)
    party = Party(members=[Player()])
    weights = _capture_weights(monkeypatch, node, party)
    assert weights.get("luna") == pytest.approx(1.0)


def test_luna_non_boss_weight_multiplier(monkeypatch) -> None:
    node = MapNode(room_id=0, room_type="normal", floor=1, index=1, loop=1, pressure=0)
    party = Party(members=[Player()])
    weights = _capture_weights(monkeypatch, node, party)
    assert weights.get("luna") == pytest.approx(5.0)


def test_luna_weighting_respects_party_ids() -> None:
    node = MapNode(room_id=0, room_type="boss", floor=3, index=1, loop=1, pressure=0)
    party_ids = {"luna", "player"}
    weight = Luna.get_spawn_weight(node=node, party_ids=party_ids, boss=True)
    assert weight == 0.0


def test_battle_utils_has_no_luna_literal() -> None:
    utils_source = Path(utils.__file__).read_text(encoding="utf-8")
    assert "luna" not in utils_source.lower()


@pytest.mark.asyncio
async def test_setup_applies_boss_scaling(monkeypatch) -> None:
    node = MapNode(room_id=0, room_type="boss", floor=3, index=1, loop=1, pressure=0)
    party = Party(members=[Player()])
    luna = Luna()
    luna.rank = "boss"

    base_stats = {
        "max_hp": luna.get_base_stat("max_hp"),
        "atk": luna.get_base_stat("atk"),
        "defense": luna.get_base_stat("defense"),
    }

    monkeypatch.setattr(battle_setup, "_scale_stats", lambda *args, **kwargs: None)

    await battle_setup.setup_battle(node, party, foe=luna)

    for stat, original in base_stats.items():
        assert luna.get_base_stat(stat) == pytest.approx(original * 4)
