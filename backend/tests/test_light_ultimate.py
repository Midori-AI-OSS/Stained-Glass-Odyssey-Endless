import pytest

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.light import Light
from plugins.dots.bleed import Bleed


class DummyPlayer(Stats):
    async def use_ultimate(self) -> bool:  # pragma: no cover
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_light_ultimate_heals_and_cleanses():
    light = Light()
    actor = DummyPlayer(damage_type=light)
    ally = Stats()
    ally.hp = 50
    ally._base_max_hp = 100
    enemy = Stats()
    enemy._base_defense = 100
    actor.effect_manager = EffectManager(actor)
    ally.effect_manager = EffectManager(ally)
    enemy.effect_manager = EffectManager(enemy)
    ally.effect_manager.add_dot(Bleed(10, 3))
    actor.add_ultimate_charge(15)
    await light.ultimate(actor, [actor, ally], [enemy])
    assert ally.hp == ally.max_hp
    assert not ally.effect_manager.dots
    assert ally.dots == []


@pytest.mark.asyncio
async def test_light_ultimate_applies_defense_debuff():
    light = Light()
    actor = DummyPlayer(damage_type=light)
    enemy = Stats()
    enemy._base_defense = 100
    actor.effect_manager = EffectManager(actor)
    enemy.effect_manager = EffectManager(enemy)
    actor.add_ultimate_charge(15)
    await light.ultimate(actor, [actor], [enemy])
    mods = [m for m in enemy.effect_manager.mods if m.id == "light_ultimate_def_down"]
    assert len(mods) == 1
    assert mods[0].turns == 10
    assert enemy.defense < 100
