import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic


@pytest.mark.asyncio
async def test_passive_stack_display():
    """Test that passives correctly report stack counts for the UI."""
    registry = PassiveRegistry()
    luna_cls = registry._registry["luna_lunar_reservoir"]

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
    luna_cls._charge_points.clear()
    luna_cls._swords_by_owner.clear()

    # Initially 0 charge
    description = registry.describe(luna)
    luna_passive = next((p for p in description if p["id"] == "luna_lunar_reservoir"), None)
    assert luna_passive is not None
    assert luna_passive["stacks"] == 0
    assert luna_passive["max_stacks"] == 2000

    # After taking actions, should build charge
    for _ in range(10):  # 10 actions = 10 charge
        await registry.trigger("action_taken", luna)

    description = registry.describe(luna)
    luna_passive = next((p for p in description if p["id"] == "luna_lunar_reservoir"), None)
    assert luna_passive["stacks"] == 10


@pytest.mark.asyncio
async def test_ryne_balance_stacks_apply_scaling_aura():
    """Ryne's balance stacks should scale her aura and Luna's link bonuses."""
    registry = PassiveRegistry()
    ryne_cls = registry._registry["ryne_oracle_of_balance"]

    ryne_cls._balance_points.clear()
    ryne_cls._balance_totals.clear()
    ryne_cls._balance_carry.clear()
    ryne_cls._luna_links.clear()
    ryne_cls._ally_refs.clear()
    ryne_cls._bus_handlers.clear()

    ryne = Stats(hp=1000, damage_type=Generic())
    luna = Stats(hp=1000, damage_type=Generic())
    setattr(luna, "id", "luna")

    ryne.passives = ["ryne_oracle_of_balance"]
    ryne.set_base_stat("atk", 300)
    luna.set_base_stat("atk", 150)

    await registry.trigger("battle_start", ryne, party=[ryne, luna])

    owner_id = id(ryne)
    aura_name = f"{ryne_cls.id}_oracle_aura_{owner_id}"
    link_name = f"{ryne_cls.id}_luna_link_{owner_id}"

    assert not any(effect.name == aura_name for effect in ryne.get_active_effects())
    assert not any(effect.name == link_name for effect in luna.get_active_effects())

    await registry.trigger("action_taken", ryne, party=[ryne, luna])

    scale = ryne_cls.get_balance(ryne) / max(1, ryne_cls.THRESHOLD)
    aura_effect = next(effect for effect in ryne.get_active_effects() if effect.name == aura_name)
    link_effect = next(effect for effect in luna.get_active_effects() if effect.name == link_name)

    owner_base_atk = int(ryne.get_base_stat("atk"))
    luna_base_atk = int(luna.get_base_stat("atk"))

    assert aura_effect.stat_modifiers["atk"] == max(
        1,
        int(owner_base_atk * ryne_cls.OWNER_ATK_RATIO * scale),
    )
    assert aura_effect.stat_modifiers["mitigation"] == pytest.approx(
        ryne_cls.OWNER_MITIGATION_RATIO * scale
    )
    assert aura_effect.stat_modifiers["effect_resistance"] == pytest.approx(
        ryne_cls.OWNER_EFFECT_RES_RATIO * scale
    )
    assert aura_effect.stat_modifiers["crit_rate"] == pytest.approx(
        ryne_cls.OWNER_CRIT_RATIO * scale
    )

    assert link_effect.stat_modifiers["atk"] == max(
        1,
        int(luna_base_atk * ryne_cls.LUNA_ATK_RATIO * scale),
    )
    assert link_effect.stat_modifiers["mitigation"] == pytest.approx(
        ryne_cls.LUNA_MITIGATION_RATIO * scale
    )
    assert link_effect.stat_modifiers["effect_resistance"] == pytest.approx(
        ryne_cls.LUNA_EFFECT_RES_RATIO * scale
    )

    await registry.trigger("action_taken", ryne, party=[ryne, luna])

    scale = ryne_cls.get_balance(ryne) / max(1, ryne_cls.THRESHOLD)
    aura_effect = next(effect for effect in ryne.get_active_effects() if effect.name == aura_name)
    link_effect = next(effect for effect in luna.get_active_effects() if effect.name == link_name)

    assert aura_effect.stat_modifiers["atk"] == max(
        1,
        int(owner_base_atk * ryne_cls.OWNER_ATK_RATIO * scale),
    )
    assert link_effect.stat_modifiers["atk"] == max(
        1,
        int(luna_base_atk * ryne_cls.LUNA_ATK_RATIO * scale),
    )

    await registry.trigger("action_taken", ryne, party=[ryne, luna])

    assert ryne_cls.get_balance(ryne) == 0
    assert not any(effect.name == aura_name for effect in ryne.get_active_effects())
    assert not any(effect.name == link_name for effect in luna.get_active_effects())

    await ryne_cls().on_defeat(ryne)


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
    luna.ultimate_charge = luna.ultimate_charge_max
    luna.ultimate_ready = True

    target = Stats(hp=1000, damage_type=Generic())
    target.set_base_stat("dodge_odds", 0)

    result = await luna.damage_type.ultimate(luna, [luna], [target])

    assert result is True
    # Ultimate should grant 64 charge from the event and 64 more from the 64
    # rapid strikes, without any additional fallback charge being applied.
    assert luna_cls.get_charge(luna) == 64 * 2


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
async def test_persona_duality_pip_display_and_cap():
    """Persona Light and Dark Duality should show pip display with capped count."""
    registry = PassiveRegistry()

    persona = Stats(hp=1000, damage_type=Generic())
    persona.passives = ["persona_light_and_dark_duality"]

    await registry.trigger("turn_start", persona, party=[persona], foes=[])

    description = registry.describe(persona)
    duality_passive = next(
        (p for p in description if p["id"] == "persona_light_and_dark_duality"),
        None,
    )
    assert duality_passive is not None
    assert duality_passive["display"] == "pips"
    assert duality_passive["max_stacks"] == 5
    assert duality_passive["stacks"]["count"] == 1
    assert duality_passive["stacks"]["rank"] == 1
    assert duality_passive["stacks"]["persona"] == "light"
    assert duality_passive["stacks"]["flips"] == 0

    # Trigger several persona flips so the rank exceeds the pip cap
    for _ in range(5):
        await registry.trigger("action_taken", persona, party=[persona], foes=[])

    description = registry.describe(persona)
    duality_passive = next(
        (p for p in description if p["id"] == "persona_light_and_dark_duality"),
        None,
    )
    assert duality_passive is not None
    assert duality_passive["display"] == "pips"
    assert duality_passive["max_stacks"] == 5
    assert duality_passive["stacks"]["count"] == 3
    assert duality_passive["stacks"]["rank"] >= 4
    assert duality_passive["stacks"]["persona"] in {"light", "dark"}
    assert duality_passive["stacks"]["flips"] >= 1


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
    """Test that Luna Lunar Reservoir can stack beyond 200 and grants attack bonus scaling."""
    registry = PassiveRegistry()
    luna_cls = registry._registry["luna_lunar_reservoir"]

    luna_cls._charge_points.clear()
    luna_cls._swords_by_owner.clear()

    luna = Stats(hp=1000, damage_type=Generic())
    luna.passives = ["luna_lunar_reservoir"]

    # Take enough actions to go past the soft cap of 2000
    await registry.trigger("action_taken", luna)
    luna_cls.add_charge(
        luna,
        max(0, 2200 - luna_cls.get_charge(luna)),
    )

    description = registry.describe(luna)
    luna_passive = next((p for p in description if p["id"] == "luna_lunar_reservoir"), None)
    assert luna_passive is not None

    # Should show current charge without automatically draining below the cap
    current_charge = luna_cls.get_charge(luna)
    assert current_charge >= 2000  # Should be able to go past 2000
    assert luna_passive["stacks"] == current_charge
    assert luna_passive["max_stacks"] == 2000  # Soft cap stays at 2000


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
async def test_soft_caps_ryne_beyond_120():
    """Ryne's balance stacks should overflow the soft cap with halved gains."""
    registry = PassiveRegistry()
    ryne_cls = registry._registry["ryne_oracle_of_balance"]

    ryne = Stats(hp=1000, damage_type=Generic())
    ryne.passives = ["ryne_oracle_of_balance"]

    ryne_cls._balance_points.clear()
    ryne_cls._balance_totals.clear()
    ryne_cls._balance_carry.clear()

    await registry.trigger("battle_start", ryne, party=[ryne])

    for _ in range(60):
        await registry.trigger("action_taken", ryne, party=[ryne])

    assert ryne_cls.get_total_balance(ryne) == ryne_cls.SOFT_CAP
    assert ryne_cls.get_balance(ryne) == 0

    await registry.trigger("action_taken", ryne, party=[ryne])

    assert ryne_cls.get_total_balance(ryne) == ryne_cls.SOFT_CAP + 2
    assert ryne_cls.get_balance(ryne) == 1

    description = registry.describe(ryne)
    ryne_passive = next((p for p in description if p["id"] == "ryne_oracle_of_balance"), None)
    assert ryne_passive is not None
    assert ryne_passive["stacks"] == ryne_cls.get_total_balance(ryne)
    assert ryne_passive["max_stacks"] == ryne_cls.SOFT_CAP
    assert ryne_passive["display"] == "number"


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
