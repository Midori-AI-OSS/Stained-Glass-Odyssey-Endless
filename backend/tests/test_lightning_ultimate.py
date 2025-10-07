import asyncio
import random

import pytest

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.lightning import Lightning
from plugins.dots.abyssal_corruption import AbyssalCorruption
from plugins.dots.blazing_torment import BlazingTorment
from plugins.dots.celestial_atrophy import CelestialAtrophy
from plugins.dots.charged_decay import ChargedDecay
from plugins.dots.frozen_wound import FrozenWound
from plugins.dots.gale_erosion import GaleErosion
from plugins.effects.aftertaste import Aftertaste


class Actor(Stats):
    async def use_ultimate(self) -> bool:
        if not getattr(self, "ultimate_ready", False):
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_lightning_ultimate_applies_random_dots(monkeypatch):
    lightning = Lightning()
    attacker = Actor()
    attacker._base_atk = 100
    attacker.damage_type = lightning
    attacker.ultimate_charge = attacker.ultimate_charge_max
    attacker.ultimate_ready = True
    target = Stats()
    target.effect_manager = EffectManager(target)

    types = ["Fire", "Ice", "Wind", "Lightning", "Light", "Dark"]
    seq = iter(types * 2)
    monkeypatch.setattr(random, "choice", lambda _seq: next(seq))

    await lightning.ultimate(attacker, [], [target])

    dot_map = {
        "Fire": BlazingTorment.id,
        "Ice": FrozenWound.id,
        "Wind": GaleErosion.id,
        "Lightning": ChargedDecay.id,
        "Light": CelestialAtrophy.id,
        "Dark": AbyssalCorruption.id,
    }
    expected = [dot_map[t] for t in types * 2][:10]
    assert [d.id for d in target.effect_manager.dots] == expected


@pytest.mark.asyncio
async def test_lightning_ultimate_aftertaste_stacks(monkeypatch):
    lightning = Lightning()
    attacker = Actor()
    attacker._base_atk = 100
    attacker.damage_type = lightning
    attacker.ultimate_charge = attacker.ultimate_charge_max
    attacker.ultimate_ready = True
    target = Stats()
    target.effect_manager = EffectManager(target)

    # Mock apply_damage to avoid async issues
    async def mock_apply_damage(damage, attacker=None, action_name=None):
        pass
    target.apply_damage = mock_apply_damage

    hits: list[int] = []

    async def fake_apply(self, atk, tgt):
        hits.append(self.hits)
        return [0] * self.hits

    monkeypatch.setattr(Aftertaste, "apply", fake_apply)

    # Test BUS directly
    simple_calls = []
    async def simple_handler(*args):
        simple_calls.append(args)

    BUS.subscribe("hit_landed", simple_handler)
    await BUS.emit_async("hit_landed", attacker, target, 10, "attack")
    await asyncio.sleep(0)
    print(f"Simple handler calls: {simple_calls}")
    assert len(simple_calls) > 0  # Verify BUS works

    # Now test the ultimate
    await lightning.ultimate(attacker, [], [target])

    # The handler should have been set up by the ultimate call
    print(f"Has handler attribute: {hasattr(attacker, '_lightning_aftertaste_handler')}")
    print(f"Stacks: {getattr(attacker, '_lightning_aftertaste_stacks', 'None')}")

    await BUS.emit_async("hit_landed", attacker, target, 10, "attack")
    await asyncio.sleep(0)
    assert hits == [1]
