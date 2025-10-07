import asyncio

import pytest

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.light import Light
from plugins.dots.bleed import Bleed
from plugins.hots.radiant_regeneration import RadiantRegeneration
from plugins.passives.normal.lady_light_radiant_aegis import LadyLightRadiantAegis


class DummyLightUser(Stats):
    async def use_ultimate(self) -> bool:  # pragma: no cover - helper for tests
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_radiant_aegis_hot_event_applies_shields():
    LadyLightRadiantAegis._attack_bonuses.clear()
    passive = LadyLightRadiantAegis()
    healer = DummyLightUser(damage_type=Light())
    healer.vitality = 1.5
    ally = Stats()
    ally.vitality = 1.25
    ally.effect_manager = EffectManager(ally)

    await passive.apply(healer)

    hot = RadiantRegeneration()
    hot.healing = 8  # Boost base healing so scaling is visible
    hot.source = healer
    ally.effect_manager.add_hot(hot)

    await asyncio.sleep(0.05)

    expected_hot = int(hot.healing * healer.vitality * ally.vitality)
    expected_shield = int(expected_hot * 0.5)
    assert ally.shields == expected_shield
    assert ally.overheal_enabled is True

    resistance_name = f"{passive.id}_hot_resistance"
    assert any(effect.name == resistance_name for effect in ally.get_active_effects())

    BUS.emit_batched("battle_end", healer)
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_radiant_aegis_dot_cleanse_triggers_on_light_ultimate():
    LadyLightRadiantAegis._attack_bonuses.clear()
    passive = LadyLightRadiantAegis()
    healer = DummyLightUser(damage_type=Light())
    ally = Stats()
    ally.hp = ally.max_hp - 100
    healer.effect_manager = EffectManager(healer)
    ally.effect_manager = EffectManager(ally)
    ally.effect_manager.add_dot(Bleed(10, 3))

    await passive.apply(healer)

    healer.add_ultimate_charge(healer.ultimate_charge_max)
    await healer.damage_type.ultimate(healer, [healer, ally], [])
    await asyncio.sleep(0.05)

    expected_attack_bonus = int(healer.atk * 0.02)
    assert LadyLightRadiantAegis.get_attack_bonus(healer) == expected_attack_bonus

    cleanse_effect_name = f"{passive.id}_cleanse_attack_{id(healer)}"
    assert any(effect.name == cleanse_effect_name for effect in healer.get_active_effects())

    BUS.emit_batched("battle_end", healer)
    await asyncio.sleep(0.05)
