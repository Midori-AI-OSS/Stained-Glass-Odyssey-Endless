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
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from autofighter.rooms.foes import SpawnTemplate  # noqa: E402
from autofighter.rooms.foes import load_catalog  # noqa: E402
from plugins.foes._base import FoeBase  # noqa: E402
from plugins.foes.slime import Slime  # noqa: E402
from plugins.players.player import Player  # noqa: E402


def test_catalog_exposes_spawn_templates_for_foes_and_players() -> None:
    templates, player_templates, adjectives = load_catalog()

    assert "slime" in templates
    slime_template = templates["slime"]
    assert isinstance(slime_template, SpawnTemplate)
    assert issubclass(slime_template.cls, FoeBase)
    assert slime_template.cls.__name__ == Slime.__name__
    assert slime_template.tags == frozenset(getattr(Slime, "spawn_tags", ()) or ())
    assert slime_template.apply_adjective is False

    assert "player" in player_templates
    player_template = player_templates["player"]
    assert player_template is templates["player"]
    assert isinstance(player_template, SpawnTemplate)
    assert player_template.tags == frozenset({"player_template"})
    assert issubclass(player_template.cls, FoeBase)
    assert player_template.cls is not Player
    assert player_template.apply_adjective is True

    assert adjectives
    assert all(isinstance(adjective, type) for adjective in adjectives)
    assert any(getattr(adjective, "id", "") == "evil" for adjective in adjectives)
