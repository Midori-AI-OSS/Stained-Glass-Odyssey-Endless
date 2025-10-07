import random
import types

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.ice import Ice


class Actor(Stats):
    async def use_ultimate(self) -> bool:
        if not self.ultimate_ready:
            return False

        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_ice_ultimate_hits_multiple_enemies_without_error():
    actor = Actor(damage_type=Ice())
    actor.id = "ice-actor"
    actor.atk = 300
    actor.ultimate_charge = actor.ultimate_charge_max
    actor.ultimate_ready = True

    random.seed(7)

    foes: list[Stats] = []
    hits: dict[str, int] = {}

    async def record_damage(self, *_args, **_kwargs):
        hits[self.id] = hits.get(self.id, 0) + 1
        return 0

    for idx, aggro in enumerate((1.0, 2.0, 6.0)):
        foe = Stats()
        foe.id = f"foe-{idx}"
        foe.defense = 0
        foe.dodge_odds = 0
        foe.apply_damage = types.MethodType(record_damage, foe)
        foe.base_aggro = aggro
        foes.append(foe)

    set_battle_active(True)
    try:
        result = await actor.damage_type.ultimate(actor, [actor], foes)
    finally:
        set_battle_active(False)

    assert result is True
    assert sum(hits.values()) == 18
    assert hits.get("foe-2", 0) > hits.get("foe-1", 0)
    assert hits.get("foe-2", 0) > hits.get("foe-0", 0)
