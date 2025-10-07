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

    foes: list[Stats] = []
    for idx in range(3):
        foe = Stats()
        foe.id = f"foe-{idx}"
        foe.defense = 0
        foe.dodge_odds = 0
        foes.append(foe)

    set_battle_active(True)
    try:
        result = await actor.damage_type.ultimate(actor, [actor], foes)
    finally:
        set_battle_active(False)

    assert result is True
    for foe in foes:
        assert foe.hp < foe.max_hp
        assert foe.last_damage_taken > 0
