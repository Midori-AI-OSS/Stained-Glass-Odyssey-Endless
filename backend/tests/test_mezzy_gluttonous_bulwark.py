import pytest

from autofighter.stats import Stats
from plugins.passives.normal.mezzy_gluttonous_bulwark import SAFE_MAX_HP_FLOOR
from plugins.passives.normal.mezzy_gluttonous_bulwark import MezzyGluttonousBulwark


@pytest.mark.asyncio
async def test_mezzy_gluttonous_bulwark_respects_max_hp_floor() -> None:
    MezzyGluttonousBulwark._siphoned_stats.clear()
    passive = MezzyGluttonousBulwark()
    mezzy = Stats()
    ally = Stats()

    initial_max_hp = ally.max_hp
    iterations = initial_max_hp * 2

    for _ in range(iterations):
        await passive.siphon_from_allies(mezzy, [ally])
        assert ally.max_hp >= SAFE_MAX_HP_FLOOR

    ally_id = id(ally)
    tracked_max_hp = passive._siphoned_stats.get(ally_id, {}).get("max_hp", 0)

    assert ally.max_hp == SAFE_MAX_HP_FLOOR
    assert tracked_max_hp == initial_max_hp - ally.max_hp
