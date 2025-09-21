from __future__ import annotations

import sys
import types
from pathlib import Path

logging_module = types.ModuleType("battle_logging")
writers_module = types.ModuleType("battle_logging.writers")
writers_module.start_battle_logging = lambda *_, **__: None
writers_module.end_battle_logging = lambda *_, **__: None
writers_module.BattleLogger = type("BattleLogger", (), {})
logging_module.writers = writers_module
sys.modules.setdefault("battle_logging", logging_module)
sys.modules.setdefault("battle_logging.writers", writers_module)
sys.modules.setdefault("services", types.ModuleType("services"))
user_level_module = types.ModuleType("services.user_level_service")
user_level_module.gain_user_exp = lambda *_, **__: None
user_level_module.get_user_level = lambda *_, **__: 1
sys.modules.setdefault("services.user_level_service", user_level_module)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import _build_foes
from autofighter.rooms.foe_factory import SpawnTemplate
from autofighter.rooms.foe_factory import get_foe_factory
from plugins.foes.slime import Slime
from plugins.players import Player


@pytest.fixture(autouse=True)
def reset_factory(monkeypatch):
    monkeypatch.setattr("autofighter.rooms.foe_factory._FACTORY", None)
    yield


def test_high_stat_scaling_obeys_diminishing_returns(monkeypatch):
    factory = get_foe_factory()

    monkeypatch.setattr("autofighter.rooms.foe_factory.random.uniform", lambda a, b: (a + b) / 2)
    monkeypatch.setattr("autofighter.rooms.foe_factory.random.randint", lambda a, b: (a + b) // 2)
    monkeypatch.setattr("autofighter.rooms.foe_factory.random.random", lambda: 0.0)

    node = MapNode(room_id=1, room_type="battle-normal", floor=5, index=10, loop=3, pressure=12)
    slime = Slime()
    slime.set_base_stat("atk", 5000)
    baseline = slime.atk

    factory.scale_stats(slime, node, strength=10.0)

    boosted = slime.atk
    assert boosted >= baseline
    assert boosted - baseline < 50


def test_build_foes_respects_recent_weights_and_exclusions(monkeypatch):
    factory = get_foe_factory()
    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    slime_template = factory.templates.get("slime")
    template_id = "slime"
    if slime_template is None:
        slime_template = SpawnTemplate(id="dummy", cls=Slime)
        template_id = "dummy"
        monkeypatch.setattr(factory, "_templates", {template_id: slime_template}, raising=False)
    else:
        monkeypatch.setattr(factory, "_templates", {template_id: slime_template}, raising=False)
    base_weight = factory._weight_for_template(
        slime_template,
        node=node,
        party_ids=set(),
        recent_ids=set(),
        boss=False,
    )
    reduced_weight = factory._weight_for_template(
        slime_template,
        node=node,
        party_ids=set(),
        recent_ids={template_id},
        boss=False,
    )
    if base_weight > 0:
        expected_reduced = max(
            base_weight * factory.config["recent_weight_factor"],
            factory.config["recent_weight_min"],
        )
        assert reduced_weight == base_weight
        assert expected_reduced < base_weight
    else:
        assert reduced_weight == base_weight

    party = Party(members=[Player()])
    foes = _build_foes(node, party, exclude_ids={template_id})
    assert all(foe.id != template_id for foe in foes)
