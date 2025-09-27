from __future__ import annotations

from pathlib import Path
import sys
import types

logging_module = types.ModuleType("battle_logging")
writers_module = types.ModuleType("battle_logging.writers")
writers_module.start_battle_logging = lambda *_, **__: None
writers_module.end_battle_logging = lambda *_, **__: None
writers_module.BattleLogger = type("BattleLogger", (), {})
writers_module.get_current_run_logger = lambda *_, **__: None
logging_module.writers = writers_module
sys.modules.setdefault("battle_logging", logging_module)
sys.modules.setdefault("battle_logging.writers", writers_module)
sys.modules.setdefault("services", types.ModuleType("services"))
user_level_module = types.ModuleType("services.user_level_service")
user_level_module.gain_user_exp = lambda *_, **__: None
user_level_module.get_user_level = lambda *_, **__: 1
sys.modules.setdefault("services.user_level_service", user_level_module)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from autofighter.mapgen import MapNode  # noqa: E402
from autofighter.party import Party  # noqa: E402
from autofighter.rooms import _build_foes  # noqa: E402
from autofighter.rooms.foe_factory import SpawnTemplate  # noqa: E402
from autofighter.rooms.foe_factory import get_foe_factory  # noqa: E402
from plugins.characters import CHARACTER_FOES  # noqa: E402
from plugins.characters import Player  # noqa: E402
from plugins.characters.slime import Slime  # noqa: E402


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
    monkeypatch.setattr("plugins.characters.ADJ_CLASSES", [], raising=False)
    slime_cls = CHARACTER_FOES[Slime.id]
    slime = slime_cls()
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
        slime_cls = CHARACTER_FOES[Slime.id]
        slime_template = SpawnTemplate(id="dummy", cls=slime_cls)
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
