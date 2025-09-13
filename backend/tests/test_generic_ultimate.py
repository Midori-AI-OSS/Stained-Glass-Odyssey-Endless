import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic
from plugins.passives.luna_lunar_reservoir import LunaLunarReservoir


class Actor(Stats):
    def use_ultimate(self) -> bool:  # pragma: no cover - simple helper
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        BUS.emit("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_generic_ultimate_hits_and_passive_triggers():
    LunaLunarReservoir._charge_points.clear()

    actor = Actor(damage_type=Generic(), passives=["luna_lunar_reservoir"])
    actor.id = "luna"
    actor._base_atk = 64
    actor._base_defense = 0
    actor._base_crit_rate = 0

    target = Stats()
    target.id = "target"
    target._base_defense = 0
    target.set_base_stat('dodge_odds', 0)

    actor.ultimate_charge = 15
    actor.ultimate_ready = True

    hits = {"count": 0}

    def count_hit(*_args):
        hits["count"] += 1

    BUS.subscribe("hit_landed", count_hit)
    try:
        result = await actor.damage_type.ultimate(actor, [actor], [target])
    finally:
        BUS.unsubscribe("hit_landed", count_hit)

    assert result is True
    assert hits["count"] == 64
    assert LunaLunarReservoir.get_charge(actor) >= 64
