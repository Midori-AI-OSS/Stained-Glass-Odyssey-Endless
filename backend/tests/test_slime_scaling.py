from pathlib import Path
import random
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

import battle_logging  # noqa: F401  # Ensure package is importable for foe factory side effects

from autofighter.mapgen import MapNode
from autofighter.rooms.foe_factory import FoeFactory
from autofighter.rooms.foes.scaling import apply_permanent_scaling
from autofighter.rooms.utils import _scale_stats
from autofighter.stats import Stats
from plugins.foes.slime import Slime


def test_slime_scaling_uses_reduced_base_stats() -> None:
    random.seed(0)

    slime = Slime()

    assert slime.max_hp == 100
    assert slime.atk == 10
    assert slime.defense == 5

    assert slime.get_base_stat("max_hp") == 100
    assert slime.get_base_stat("atk") == 10
    assert slime.get_base_stat("defense") == 5

    node = MapNode(
        room_id=1,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )

    _scale_stats(slime, node)

    assert slime.max_hp == 53
    assert slime.atk == 5
    assert slime.defense == 0


def test_slime_room_scaling_respects_plugin_baseline() -> None:
    random.seed(0)

    slime = Slime()

    nerfed_hp = slime.max_hp
    nerfed_atk = slime.atk
    nerfed_def = slime.defense

    template_hp = type(slime).base_max_hp
    template_atk = type(slime).base_atk
    template_def = type(slime).base_defense

    node = MapNode(
        room_id=1,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )

    factory = FoeFactory()
    factory.scale_stats(slime, node)

    assert slime.max_hp > 0
    assert slime.atk > 0
    assert slime.defense >= 0

    assert abs(slime.max_hp - nerfed_hp) < abs(slime.max_hp - template_hp)
    assert abs(slime.atk - nerfed_atk) < abs(slime.atk - template_atk)
    assert abs(slime.defense - nerfed_def) <= abs(slime.defense - template_def)

    assert abs(slime.get_base_stat("atk") - nerfed_atk) < abs(slime.get_base_stat("atk") - template_atk)
    assert abs(slime.get_base_stat("defense") - nerfed_def) <= abs(slime.get_base_stat("defense") - template_def)


def test_apply_permanent_scaling_skips_unknown_stats() -> None:
    stats = Stats()

    effect = apply_permanent_scaling(
        stats,
        multipliers={"nonexistent": 2.0},
        name="Unknown stat",
        modifier_id="test_unknown_stat",
    )

    assert effect is None
    assert not hasattr(stats, "_pending_mods")
