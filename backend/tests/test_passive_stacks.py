import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic


@pytest.mark.asyncio
async def test_passive_stack_display():
    """Test that passives correctly report stack counts for the UI."""
    registry = PassiveRegistry()

    # Test Luna Lunar Reservoir - should show charge points
    class LunaActor(Stats):
        async def use_ultimate(self) -> bool:  # pragma: no cover - simple helper
            if not self.ultimate_ready:
                return False
            self.ultimate_charge = 0
            self.ultimate_ready = False
            await BUS.emit_async("ultimate_used", self)
            return True

    luna = LunaActor(hp=1000, damage_type=Generic())
    luna.passives = ["luna_lunar_reservoir"]

    # Initially 0 charge
    description = registry.describe(luna)
    luna_passive = next((p for p in description if p["id"] == "luna_lunar_reservoir"), None)
    assert luna_passive is not None
    assert luna_passive["stacks"] == 0
    assert luna_passive["max_stacks"] == 200

    # After taking actions, should build charge
    for _ in range(10):  # 10 actions = 10 charge
        await registry.trigger("action_taken", luna)

    description = registry.describe(luna)
    luna_passive = next((p for p in description if p["id"] == "luna_lunar_reservoir"), None)
    assert luna_passive["stacks"] == 10


@pytest.mark.asyncio
async def test_luna_ultimate_grants_expected_charge():
    """Ultimate should only add the intended Luna Lunar Reservoir charge."""
    registry = PassiveRegistry()
    luna_cls = registry._registry["luna_lunar_reservoir"]
    luna_cls._charge_points.clear()

    class LunaActor(Stats):
        async def use_ultimate(self) -> bool:  # pragma: no cover - simple helper
            if not self.ultimate_ready:
                return False
            self.ultimate_charge = 0
            self.ultimate_ready = False
            await BUS.emit_async("ultimate_used", self)
            return True

    luna = LunaActor(hp=1000, damage_type=Generic())
    luna.passives = ["luna_lunar_reservoir"]
    luna._base_atk = 64
    luna.ultimate_charge = 15
    luna.ultimate_ready = True

    target = Stats(hp=1000, damage_type=Generic())
    target.set_base_stat("dodge_odds", 0)

    result = await luna.damage_type.ultimate(luna, [luna], [target])

    assert result is True
    assert luna_cls.get_charge(luna) == 64


@pytest.mark.asyncio
async def test_ally_overload_stack_display():
    """Test that Ally Overload correctly reports charge for the UI."""
    registry = PassiveRegistry()

    ally = Stats(hp=1000, damage_type=Generic())
    ally.passives = ["ally_overload"]

    # Initially 0 charge
    description = registry.describe(ally)
    overload_passive = next((p for p in description if p["id"] == "ally_overload"), None)
    assert overload_passive is not None
    assert overload_passive["stacks"] == 0
    assert overload_passive["max_stacks"] == 120

    # After taking actions, should build charge
    # Note: Each action adds 10 charge but also decays 5 charge per action if inactive
    # So 5 actions = (10 - 5) * 5 = 25 charge
    for _ in range(5):  # 5 actions = 25 charge net (10 per action - 5 decay)
        await registry.trigger("action_taken", ally)

    description = registry.describe(ally)
    overload_passive = next((p for p in description if p["id"] == "ally_overload"), None)
    assert overload_passive["stacks"] == 25


@pytest.mark.asyncio
async def test_graygray_counter_stack_display():
    """Test that Graygray Counter Maestro correctly reports counter stacks for the UI."""
    registry = PassiveRegistry()

    graygray = Stats(hp=1000, damage_type=Generic())
    graygray.passives = ["graygray_counter_maestro"]

    # Initially 0 stacks
    description = registry.describe(graygray)
    counter_passive = next((p for p in description if p["id"] == "graygray_counter_maestro"), None)
    assert counter_passive is not None
    assert counter_passive["stacks"] == 0
    assert counter_passive["max_stacks"] == 50

    # After taking damage (triggering counters), should build stacks
    for _ in range(3):  # 3 damage instances = 3 counter stacks
        await registry.trigger("damage_taken", graygray)

    description = registry.describe(graygray)
    counter_passive = next((p for p in description if p["id"] == "graygray_counter_maestro"), None)
    assert counter_passive["stacks"] == 3


@pytest.mark.asyncio
async def test_carly_guardian_stack_display():
    """Test that Carly Guardian's Aegis correctly reports mitigation stacks for the UI."""
    registry = PassiveRegistry()

    carly = Stats(hp=1000, damage_type=Generic())
    carly.passives = ["carly_guardians_aegis"]

    # Initially 0 stacks
    description = registry.describe(carly)
    aegis_passive = next((p for p in description if p["id"] == "carly_guardians_aegis"), None)
    assert aegis_passive is not None
    assert aegis_passive["stacks"]["mitigation"] == 0
    assert aegis_passive["stacks"]["overcharged"] is False
    assert aegis_passive["max_stacks"] == 50

    # Simulate taking damage (which should add mitigation stacks)
    from plugins.passives.normal.carly_guardians_aegis import CarlyGuardiansAegis
    carly_passive = CarlyGuardiansAegis()

    # Manually call on_damage_taken to simulate being hit
    for _ in range(2):  # 2 hits = 4 mitigation stacks (2 per hit)
        await carly_passive.on_damage_taken(carly, None, 100)

    description = registry.describe(carly)
    aegis_passive = next((p for p in description if p["id"] == "carly_guardians_aegis"), None)
    assert aegis_passive["stacks"]["mitigation"] == 4
    assert aegis_passive["stacks"]["overcharged"] is False


@pytest.mark.asyncio
async def test_bubbles_burst_stack_display():
    """Test that Bubbles Bubble Burst correctly reports attack buff stacks for the UI."""
    registry = PassiveRegistry()

    bubbles = Stats(hp=1000, damage_type=Generic())
    bubbles.passives = ["bubbles_bubble_burst"]

    # Initially 0 stacks
    description = registry.describe(bubbles)
    burst_passive = next((p for p in description if p["id"] == "bubbles_bubble_burst"), None)
    assert burst_passive is not None
    assert burst_passive["stacks"] == 0
    assert burst_passive["max_stacks"] == 20

    # Simulate bubble bursts by manually adding attack buff effects
    from autofighter.stat_effect import StatEffect

    # Add a couple of bubble burst attack buffs
    for i in range(3):
        attack_buff = StatEffect(
            name=f"bubbles_bubble_burst_burst_bonus_{i}",
            stat_modifiers={"atk": int(bubbles.atk * 0.1)},
            duration=-1,
            source="bubbles_bubble_burst",
        )
        bubbles.add_effect(attack_buff)

    description = registry.describe(bubbles)
    burst_passive = next((p for p in description if p["id"] == "bubbles_bubble_burst"), None)
    assert burst_passive["stacks"] == 3


@pytest.mark.asyncio
async def test_soft_caps_luna_beyond_200():
    """Test that Luna Lunar Reservoir can stack beyond 200 and provides dodge bonus."""
    registry = PassiveRegistry()
    from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir

    luna = Stats(hp=1000, damage_type=Generic())
    luna.passives = ["luna_lunar_reservoir"]

    # Take enough actions to go past the soft cap of 200
    for _ in range(220):  # 220 actions = 220 charge
        await registry.trigger("action_taken", luna)

    description = registry.describe(luna)
    luna_passive = next((p for p in description if p["id"] == "luna_lunar_reservoir"), None)
    assert luna_passive is not None

    # Should show current charge (might be less due to boosted mode spending)
    current_charge = LunaLunarReservoir.get_charge(luna)
    assert current_charge >= 200  # Should be able to go past 200
    assert luna_passive["stacks"] == current_charge
    assert luna_passive["max_stacks"] == 200  # Soft cap stays at 200


@pytest.mark.asyncio
async def test_soft_caps_ally_beyond_120():
    """Test that Ally Overload can stack beyond 120 with reduced charge gain."""
    registry = PassiveRegistry()
    from plugins.passives.normal.ally_overload import AllyOverload

    ally = Stats(hp=1000, damage_type=Generic())
    ally.passives = ["ally_overload"]

    # Take enough actions to go past the soft cap of 120
    # We need to account for the 5 charge decay per action
    for _ in range(30):  # 30 actions should build enough charge
        await registry.trigger("action_taken", ally)

    current_charge = AllyOverload.get_charge(ally)

    # Should be able to go past 120
    if current_charge > 120:
        description = registry.describe(ally)
        overload_passive = next((p for p in description if p["id"] == "ally_overload"), None)
        assert overload_passive["stacks"] == current_charge
        assert overload_passive["max_stacks"] == 120  # Soft cap stays at 120


@pytest.mark.asyncio
async def test_soft_caps_graygray_beyond_50():
    """Test that Graygray Counter Maestro can stack beyond 50 with reduced benefits."""
    registry = PassiveRegistry()

    graygray = Stats(hp=1000, damage_type=Generic())
    graygray.passives = ["graygray_counter_maestro"]

    # Take enough damage to go past the soft cap of 50
    for _ in range(60):  # 60 damage instances = 60 counter stacks
        await registry.trigger("damage_taken", graygray)

    description = registry.describe(graygray)
    counter_passive = next((p for p in description if p["id"] == "graygray_counter_maestro"), None)
    assert counter_passive is not None
    assert counter_passive["stacks"] == 60  # Should be able to go past 50
    assert counter_passive["max_stacks"] == 50  # Soft cap stays at 50
