from pathlib import Path
import random
import sys

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.append(str(_PROJECT_ROOT))

from autofighter.mapgen import MapNode  # noqa: E402
from autofighter.rooms.utils import _scale_stats  # noqa: E402
from plugins.players.bubbles import Bubbles  # noqa: E402
from plugins.players.luna import Luna  # noqa: E402


def _scale_player(cls, rank: str, seed: int):
    random.seed(seed)
    node = MapNode(
        room_id=1,
        room_type="battle-boss",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )

    player = cls()
    player.rank = rank
    _scale_stats(player, node)
    return player


def test_luna_boss_scaling_multiplier_applied() -> None:
    normal = _scale_player(Luna, "normal", seed=123)
    boss = _scale_player(Luna, "boss", seed=123)

    assert boss.get_base_stat("max_hp") == normal.get_base_stat("max_hp") * 4
    assert boss.get_base_stat("atk") == normal.get_base_stat("atk") * 4
    assert boss.get_base_stat("defense") == normal.get_base_stat("defense") * 4
    assert boss.hp == boss.max_hp


def test_luna_glitched_boss_scaling_multiplier_applied() -> None:
    normal = _scale_player(Luna, "normal", seed=456)
    glitched = _scale_player(Luna, "glitched boss", seed=456)

    assert glitched.get_base_stat("max_hp") == normal.get_base_stat("max_hp") * 11
    assert glitched.get_base_stat("atk") == normal.get_base_stat("atk") * 11
    assert glitched.get_base_stat("defense") == normal.get_base_stat("defense") * 11
    assert glitched.hp == glitched.max_hp


def test_other_player_boss_rank_unscaled() -> None:
    normal = _scale_player(Bubbles, "normal", seed=789)
    boss = _scale_player(Bubbles, "boss", seed=789)

    assert boss.get_base_stat("max_hp") == normal.get_base_stat("max_hp")
    assert boss.get_base_stat("atk") == normal.get_base_stat("atk")
    assert boss.get_base_stat("defense") == normal.get_base_stat("defense")
