"""
Tests for the unified summons system.
"""

import asyncio
import copy
from pathlib import Path
import random
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import llms.torch_checker as torch_checker

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import BattleRoom
from autofighter.stats import BUS
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager
from plugins.cards.phantom_ally import PhantomAlly
from plugins.characters.ally import Ally
from plugins.characters.becca import Becca
from plugins.characters.foe_base import FoeBase
from plugins.damage_types.lightning import Lightning
from plugins.passives.normal.becca_menagerie_bond import BeccaMenagerieBond


def _reset_becca_passive_state() -> None:
    """Clear global Becca Menagerie Bond tracking between tests."""

    for store in (
        BeccaMenagerieBond._summon_cooldown,
        BeccaMenagerieBond._spirit_stacks,
        BeccaMenagerieBond._last_summon,
        BeccaMenagerieBond._applied_spirit_stacks,
        BeccaMenagerieBond._buffed_summons,
    ):
        store.clear()


@pytest.mark.asyncio
async def test_summon_creation_basic(monkeypatch):
    """Test basic summon creation with stat inheritance."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Create summoner
    summoner = Ally()
    summoner.id = "test_summoner"
    summoner.ensure_permanent_summon_slots(1)
    # Set base stats directly
    summoner._base_atk = 100
    summoner._base_max_hp = 200
    summoner._base_defense = 50

    # Create summon
    summon = await Summon.create_from_summoner(
        summoner=summoner,
        summon_type="test",
        source="test_source",
        stat_multiplier=0.5
    )

    # Verify stat inheritance
    assert summon.atk == 50  # 50% of 100
    assert summon.max_hp == 100  # 50% of 200
    assert summon.hp == summon.max_hp  # Summon spawns at full health
    assert summon.defense == 25  # 50% of 50
    assert summon.summoner_id == "test_summoner"
    assert summon.summon_type == "test"
    assert summon.summon_source == "test_source"
    assert summon.id == "test_summoner_test_summon"


@pytest.mark.asyncio
async def test_summon_manager_creation_and_tracking(monkeypatch):
    """Test SummonManager summon creation and tracking."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Clean up any existing state
    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner.ensure_permanent_summon_slots(1)
    summoner.ensure_permanent_summon_slots(1)
    summoner.ensure_permanent_summon_slots(1)

    # Create summon via manager
    summon = await SummonManager.create_summon(
        summoner=summoner,
        summon_type="test",
        source="test_source"
    )

    assert summon is not None
    assert summon.hp == summon.max_hp
    assert summon.summoner_id == "test_summoner"

    # Verify tracking
    tracked_summons = SummonManager.get_summons("test_summoner")
    assert len(tracked_summons) == 1
    assert tracked_summons[0].id == summon.id


@pytest.mark.asyncio
async def test_summon_manager_limits(monkeypatch):
    """Test summon limits are enforced."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner.ensure_permanent_summon_slots(1)
    summoner.ensure_permanent_summon_slots(1)

    # Create first summon (should succeed)
    summon1 = await SummonManager.create_summon(
        summoner=summoner,
        summon_type="test1",
        source="test_source",
    )
    assert summon1 is not None

    # Try to create second summon (should fail due to limit)
    summon2 = await SummonManager.create_summon(
        summoner=summoner,
        summon_type="test2",
        source="test_source",
    )
    assert summon2 is None

    # Should still only have one summon
    tracked_summons = SummonManager.get_summons("test_summoner")
    assert len(tracked_summons) == 1


@pytest.mark.asyncio
async def test_summon_battle_lifecycle(monkeypatch):
    """Test summon cleanup during battle events."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner.ensure_permanent_summon_slots(1)

    # Create temporary summon
    summon = await SummonManager.create_summon(
        summoner=summoner,
        summon_type="temporary",
        source="test_source",
        turns_remaining=1
    )
    assert summon is not None

    # Should be tracked
    assert len(SummonManager.get_summons("test_summoner")) == 1

    # Emit battle end - temporary summons should be cleaned up
    await BUS.emit_async("battle_end", FoeBase())

    # Should be removed
    assert len(SummonManager.get_summons("test_summoner")) == 0


@pytest.mark.asyncio
async def test_summon_turn_expiration(monkeypatch):
    """Test summon expiration based on turn count."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner.ensure_permanent_summon_slots(1)

    # Create summon with 2 turn duration
    summon = await SummonManager.create_summon(
        summoner=summoner,
        summon_type="timed",
        source="test_source",
        turns_remaining=2
    )

    assert len(SummonManager.get_summons("test_summoner")) == 1

    # First turn
    await BUS.emit_async("turn_start", summoner)
    assert len(SummonManager.get_summons("test_summoner")) == 1
    assert summon.turns_remaining == 1

    # Second turn - should expire
    await BUS.emit_async("turn_start", summoner)
    assert len(SummonManager.get_summons("test_summoner")) == 0


@pytest.mark.asyncio
async def test_phantom_ally_new_system(monkeypatch):
    """Test PhantomAlly card using new summons system."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    # Create party
    ally = Ally()
    ally.id = "ally"
    lightning = Lightning()
    ally.damage_type = lightning
    ally.ensure_permanent_summon_slots(1)
    becca = Becca()
    becca.id = "becca"
    party = Party(members=[ally, becca])

    # Apply PhantomAlly card
    monkeypatch.setattr(random, "choice", lambda members: ally)
    await PhantomAlly().apply(party)

    # Should have 3 members now (2 original + 1 phantom)
    assert len(party.members) == 3

    # One should be a phantom summon
    phantom = None
    for member in party.members:
        if hasattr(member, 'summon_type') and member.summon_type == "phantom":
            phantom = member
            break

    assert phantom is not None
    assert phantom.summon_source == "phantom_ally"
    assert phantom.turns_remaining == -1  # Should last the entire battle
    assert getattr(phantom, "damage_type", None) is not None
    assert getattr(phantom.damage_type, "id", None) == lightning.id


@pytest.mark.asyncio
async def test_becca_menagerie_bond_persists_between_battles(monkeypatch):
    """Becca's passive should retain summon history across battle clones."""

    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    _reset_becca_passive_state()
    SummonManager.reset_all()

    passive = BeccaMenagerieBond()
    template_becca = Becca()
    template_becca.id = "becca_passive_persistence"

    battle_one_becca = copy.deepcopy(template_becca)
    await passive.apply(battle_one_becca)

    assert await passive.summon_jellyfish(battle_one_becca, jellyfish_type="electric")

    key = BeccaMenagerieBond._resolve_entity_key(battle_one_becca)
    passive._summon_cooldown[key] = 0

    assert await passive.summon_jellyfish(battle_one_becca, jellyfish_type="poison")

    assert BeccaMenagerieBond.get_spirit_stacks(battle_one_becca) == 1
    assert BeccaMenagerieBond.get_last_summon_type(battle_one_becca) == "poison"

    SummonManager.reset_all()

    battle_two_becca = copy.deepcopy(template_becca)
    await passive.apply(battle_two_becca)

    assert BeccaMenagerieBond.get_spirit_stacks(battle_two_becca) == 1
    assert BeccaMenagerieBond.get_last_summon_type(battle_two_becca) == "poison"
    assert BeccaMenagerieBond.get_active_summon_type(battle_two_becca) is None

    _reset_becca_passive_state()
    SummonManager.reset_all()


@pytest.mark.asyncio
async def test_becca_jellyfish_after_phantom(monkeypatch):
    """Becca can still summon a jellyfish after Phantom Ally adds a copy."""

    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    _reset_becca_passive_state()
    SummonManager.cleanup()

    becca = Becca()
    becca.id = "becca"
    becca.hp = 100
    becca._base_max_hp = 100

    party = Party(members=[becca])

    passive = BeccaMenagerieBond()
    await passive.apply(becca)

    await PhantomAlly().apply(party)

    phantom_present = any(
        getattr(member, "summon_source", "") == "phantom_ally" for member in party.members
    )
    assert phantom_present

    success = await passive.summon_jellyfish(becca, party=party)
    assert success is True

    summons = SummonManager.get_summons("becca")
    assert any(s.summon_source == passive.id for s in summons)


@pytest.mark.asyncio
async def test_becca_jellyfish_summoning(monkeypatch):
    """Test Becca's jellyfish summoning using new system."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    _reset_becca_passive_state()
    SummonManager.cleanup()

    # Create Becca
    becca = Becca()
    becca.id = "becca"
    becca.hp = 100
    becca._base_max_hp = 100

    # Create passive instance
    passive = BeccaMenagerieBond()

    # Test jellyfish summoning
    success = await passive.summon_jellyfish(becca, "electric")
    assert success is True

    # Should have paid HP cost
    assert becca.hp == 90  # 100 - 10% = 90

    # Should have created summon
    summons = SummonManager.get_summons("becca")
    assert len(summons) == 1

    jellyfish = summons[0]
    assert jellyfish.summon_type == "jellyfish_electric"
    assert jellyfish.summon_source == "becca_menagerie_bond"
    assert jellyfish.damage_type.__class__.__name__ == "Lightning"


@pytest.mark.asyncio
async def test_becca_summon_added_to_party(monkeypatch):
    """Summoning a jellyfish adds it to the party for battle."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    _reset_becca_passive_state()
    SummonManager.cleanup()

    becca = Becca()
    becca.id = "becca"
    party = Party(members=[becca])

    passive = BeccaMenagerieBond()

    await passive.summon_jellyfish(becca, "electric", party)

    # Party should now include the summon
    assert len(party.members) == 2
    summon = next(m for m in party.members if m is not becca)
    assert summon.summon_source == "becca_menagerie_bond"


@pytest.mark.asyncio
async def test_collect_summons_grouped_by_owner(monkeypatch):
    """Ensure snapshot helper groups summons by summoner id."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    _reset_becca_passive_state()
    SummonManager.cleanup()

    becca = Becca()
    becca.id = "becca"
    party = Party(members=[becca])
    passive = BeccaMenagerieBond()

    await passive.summon_jellyfish(becca, "electric", party)

    from services.room_service import _collect_summons

    grouped = _collect_summons(party.members)
    assert "becca" in grouped
    assert len(grouped["becca"]) == 1
    assert grouped["becca"][0]["owner_id"] == "becca"


@pytest.mark.asyncio
async def test_becca_jellyfish_replacement_creates_spirit(monkeypatch):
    """Test that replacing jellyfish creates spirit stacks."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    _reset_becca_passive_state()
    SummonManager.cleanup()

    # Create Becca
    becca = Becca()
    becca.id = "becca"
    becca.hp = 100
    becca._base_max_hp = 100

    passive = BeccaMenagerieBond()

    # Summon first jellyfish
    await passive.summon_jellyfish(becca, "electric")
    assert passive.get_spirit_stacks(becca) == 0

    # Wait for cooldown
    passive._summon_cooldown[BeccaMenagerieBond._resolve_entity_key(becca)] = 0
    becca.hp = 100  # Reset HP

    # Summon different jellyfish (should create spirit)
    await passive.summon_jellyfish(becca, "healing")
    assert passive.get_spirit_stacks(becca) == 1

    # Should still have one summon (replaced)
    summons = SummonManager.get_summons("becca")
    assert len(summons) == 1
    assert summons[0].summon_type == "jellyfish_healing"


@pytest.mark.asyncio
async def test_spirit_spawn_on_summon_defeat(monkeypatch):
    """Becca gains a spirit stack when her jellyfish is defeated."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    _reset_becca_passive_state()
    SummonManager.cleanup()

    becca = Becca()
    becca.id = "becca"
    becca.hp = 100
    becca._base_max_hp = 100

    passive = BeccaMenagerieBond()

    await passive.summon_jellyfish(becca, "electric")
    assert passive.get_spirit_stacks(becca) == 0

    summon = SummonManager.get_summons("becca")[0]
    summon.hp = 0
    await SummonManager._on_entity_killed(summon)

    assert SummonManager.get_summons("becca") == []
    assert passive.get_spirit_stacks(becca) == 1


@pytest.mark.asyncio
async def test_damage_type_inheritance(monkeypatch):
    """Test that summons inherit damage types correctly."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    # Create summoner with Lightning damage type
    summoner = Ally()
    summoner.id = "lightning_summoner"
    summoner.damage_type = Lightning()

    # Create multiple summons to test probability
    lightning_count = 0
    total_summons = 20

    for i in range(total_summons):
        summon = await Summon.create_from_summoner(
            summoner=summoner,
            summon_type=f"test_{i}",
            source="test"
        )
        if summon.damage_type.__class__.__name__ == "Lightning":
            lightning_count += 1

    # Should have high percentage of Lightning damage types (around 70%)
    # Allow some variance due to randomness - at least 30% should be Lightning
    assert lightning_count >= 6  # At least 30% should be Lightning (lower bound due to randomness)


@pytest.mark.asyncio
async def test_summon_party_integration(monkeypatch):
    """Test that summons are properly added to parties for battle."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    # Create party
    ally = Ally()
    ally.id = "ally"
    ally.ensure_permanent_summon_slots(1)
    party = Party(members=[ally])

    # Create summon
    summon = await SummonManager.create_summon(
        summoner=ally,
        summon_type="test",
        source="test_source"
    )

    # Add summons to party
    added = SummonManager.add_summons_to_party(party)

    assert added == 1
    assert len(party.members) == 2
    assert summon in party.members


@pytest.mark.asyncio
async def test_summon_defeat_cleanup(monkeypatch):
    """Test that summons are cleaned up when summoner is defeated."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner.ensure_permanent_summon_slots(1)
    summoner.hp = 1

    # Create summon
    await SummonManager.create_summon(
        summoner=summoner,
        summon_type="test",
        source="test_source"
    )

    assert len(SummonManager.get_summons("test_summoner")) == 1

    # Apply lethal damage; defeat event should fire and clean up summons
    from autofighter.stats import set_battle_active

    set_battle_active(True)
    await summoner.apply_damage(summoner.hp, None)
    set_battle_active(False)

    assert len(SummonManager.get_summons("test_summoner")) == 0


@pytest.mark.asyncio
async def test_summons_reset_before_new_battle(monkeypatch):
    """A new battle should start with no leftover summons."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    async def fast_sleep(*_, **__):
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"

    await SummonManager.create_summon(
        summoner=summoner,
        summon_type="test",
        source="test_source",
    )

    assert SummonManager._active_summons

    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=0, loop=1, pressure=0)
    room = BattleRoom(node)
    foe = FoeBase()
    foe.id = "foe"
    foe.hp = 0
    party = Party(members=[summoner])

    progress_called = False

    async def progress(_):
        nonlocal progress_called
        progress_called = True
        assert not SummonManager._active_summons

    await room.resolve(party, {}, progress=progress, foe=foe)
    assert progress_called

@pytest.mark.asyncio
async def test_summon_inheritance_with_effects(monkeypatch):
    """Test that summons inherit base stats, not runtime stats affected by temporary effects."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Create summoner with specific base stats
    summoner = Ally()
    summoner.id = "test_summoner"
    summoner._base_defense = 100
    summoner._base_mitigation = 2.0
    summoner._base_vitality = 1.5

    # Add a temporary effect that boosts stats
    from autofighter.stat_effect import StatEffect
    boost_effect = StatEffect(
        name="test_boost",
        stat_modifiers={
            "defense": 50,       # +50 defense
            "mitigation": 1.0,   # +1.0 mitigation
            "vitality": 0.5      # +0.5 vitality
        },
        duration=5,
        source="test_card"
    )
    summoner.add_effect(boost_effect)

    # Verify effect is applied to runtime stats
    assert summoner.defense == 150  # 100 base + 50 effect
    assert summoner.mitigation == 3.0  # 2.0 base + 1.0 effect
    assert summoner.vitality == 2.0  # 1.5 base + 0.5 effect

    # Create summon with 50% stat inheritance
    summon = await Summon.create_from_summoner(
        summoner=summoner,
        summon_type="test",
        source="test_source",
        stat_multiplier=0.5
    )

    # Summon should inherit from BASE stats only, ignoring temporary effects
    assert summon._base_defense == 50  # 50% of base 100 (ignores +50 effect)
    assert summon._base_mitigation == 1.0  # 50% of base 2.0 (ignores +1.0 effect)
    assert summon._base_vitality == 0.75  # 50% of base 1.5 (ignores +0.5 effect)

    # Runtime stats should include inherited beneficial effects
    # The summon inherits the beneficial StatEffect, which adds +25 defense, +0.5 mitigation, +0.25 vitality
    assert summon.defense == 75  # 50 base + 25 inherited effect (50% of +50)
    assert summon.mitigation == 1.5  # 1.0 base + 0.5 inherited effect (50% of +1.0)
    assert summon.vitality == 1.0  # 0.75 base + 0.25 inherited effect (50% of +0.5)


@pytest.mark.asyncio
async def test_summon_inherits_beneficial_effects(monkeypatch):
    """Test that summons inherit beneficial effects (buffs and HOTs) but not harmful effects (DOTs)."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Create summoner
    summoner = Ally()
    summoner.id = "test_summoner"
    summoner._base_defense = 100
    summoner._base_atk = 200

    # Add beneficial StatEffect (buff)
    from autofighter.stat_effect import StatEffect
    buff_effect = StatEffect(
        name="test_buff",
        stat_modifiers={
            "atk": 50,       # +50 attack - beneficial
            "defense": 25,   # +25 defense - beneficial
        },
        duration=5,
        source="test_card"
    )
    summoner.add_effect(buff_effect)

    # Add EffectManager with HOT and StatModifier
    from autofighter.effects import EffectManager
    from autofighter.effects import HealingOverTime
    from autofighter.effects import StatModifier
    summoner.effect_manager = EffectManager(summoner)

    # Add HOT (beneficial)
    hot = HealingOverTime(
        name="test_hot",
        healing=100,
        turns=3,
        id="test_hot_id",
        source=summoner
    )
    await summoner.effect_manager.add_hot(hot)

    # Add beneficial StatModifier
    stat_mod = StatModifier(
        stats=summoner,
        name="test_stat_buff",
        turns=4,
        id="test_stat_buff_id",
        deltas={"crit_rate": 0.1},  # +10% crit rate - beneficial
        multipliers={"crit_damage": 1.5}  # 1.5x crit damage - beneficial
    )
    await summoner.effect_manager.add_modifier(stat_mod)

    # Create summon with 50% stat inheritance
    summon = await Summon.create_from_summoner(
        summoner=summoner,
        summon_type="test",
        source="test_source",
        stat_multiplier=0.5
    )

    # Verify summon inherited beneficial StatEffect
    summon_effects = summon.get_active_effects()
    assert len(summon_effects) == 2  # One from StatEffect inheritance, one from StatModifier application

    # Find the inherited StatEffect (from summoner's StatEffect)
    stat_effect = next((e for e in summon_effects if e.name == "summon_test_buff"), None)
    assert stat_effect is not None
    assert stat_effect.stat_modifiers["atk"] == 25  # 50% of 50
    assert stat_effect.stat_modifiers["defense"] == 12.5  # 50% of 25
    assert stat_effect.duration == 5  # Same duration

    # Find the StatEffect created by the applied StatModifier
    modifier_effect = next((e for e in summon_effects if e.name == "summon_test_stat_buff_id"), None)
    assert modifier_effect is not None
    assert modifier_effect.stat_modifiers["crit_rate"] == 0.05  # 50% of 0.1
    assert modifier_effect.stat_modifiers["crit_damage"] == 0.25  # scaled multiplier bonus
    assert modifier_effect.duration == 4  # Same duration

    # Verify summon has effect manager
    assert hasattr(summon, 'effect_manager')
    assert summon.effect_manager is not None

    # Verify summon inherited HOT
    summon_hots = summon.effect_manager.hots
    assert len(summon_hots) == 1
    inherited_hot = summon_hots[0]
    assert inherited_hot.name == "summon_test_hot"
    assert inherited_hot.healing == 50  # 50% of 100
    assert inherited_hot.turns == 3  # Same duration

    # Verify summon inherited beneficial StatModifier
    summon_mods = summon.effect_manager.mods
    assert len(summon_mods) == 1
    inherited_mod = summon_mods[0]
    assert inherited_mod.name == "summon_test_stat_buff"
    assert inherited_mod.deltas["crit_rate"] == 0.05  # 50% of 0.1
    assert inherited_mod.multipliers["crit_damage"] == 1.25  # 1 + (0.5 * 0.5) bonus scaling
    assert inherited_mod.turns == 4  # Same duration


@pytest.mark.asyncio
async def test_summon_does_not_inherit_harmful_effects(monkeypatch):
    """Test that summons do NOT inherit harmful effects (DOTs, debuffs)."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Create summoner
    summoner = Ally()
    summoner.id = "test_summoner"

    # Add harmful StatEffect (debuff)
    from autofighter.stat_effect import StatEffect
    debuff_effect = StatEffect(
        name="test_debuff",
        stat_modifiers={
            "atk": -50,      # -50 attack - harmful
            "defense": -25,  # -25 defense - harmful
        },
        duration=3,
        source="enemy_curse"
    )
    summoner.add_effect(debuff_effect)

    # Add EffectManager with DOT and harmful StatModifier
    from autofighter.effects import DamageOverTime
    from autofighter.effects import EffectManager
    from autofighter.effects import StatModifier
    summoner.effect_manager = EffectManager(summoner)

    # Add DOT (harmful)
    dot = DamageOverTime(
        name="test_dot",
        damage=50,
        turns=3,
        id="test_dot_id",
        source=summoner
    )
    summoner.effect_manager.add_dot(dot)

    # Add harmful StatModifier
    harmful_mod = StatModifier(
        stats=summoner,
        name="test_stat_debuff",
        turns=4,
        id="test_stat_debuff_id",
        deltas={"crit_rate": -0.1},  # -10% crit rate - harmful
        multipliers={"crit_damage": 0.5}  # 0.5x crit damage - harmful
    )
    await summoner.effect_manager.add_modifier(harmful_mod)

    # Create summon
    summon = await Summon.create_from_summoner(
        summoner=summoner,
        summon_type="test",
        source="test_source",
        stat_multiplier=0.5
    )

    # Verify summon did NOT inherit harmful StatEffect
    summon_effects = summon.get_active_effects()
    assert len(summon_effects) == 0  # No harmful effects should be inherited

    # Verify summon has effect manager but no harmful effects
    assert hasattr(summon, 'effect_manager')

    # Verify summon did NOT inherit DOT
    summon_dots = summon.effect_manager.dots
    assert len(summon_dots) == 0  # No DOTs should be inherited

    # Verify summon did NOT inherit harmful StatModifier
    summon_mods = summon.effect_manager.mods
    assert len(summon_mods) == 0  # No harmful modifiers should be inherited


@pytest.mark.asyncio
async def test_summon_inherits_mixed_effects_correctly(monkeypatch):
    """Test that summons inherit only beneficial parts when summoner has mixed effects."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Create summoner
    summoner = Ally()
    summoner.id = "test_summoner"

    # Add mixed StatEffect (some beneficial, some harmful modifiers)
    from autofighter.stat_effect import StatEffect
    mixed_effect = StatEffect(
        name="mixed_effect",
        stat_modifiers={
            "atk": 100,      # +100 attack - beneficial
            "defense": -50,  # -50 defense - harmful
        },
        duration=3,
        source="complex_spell"
    )
    summoner.add_effect(mixed_effect)

    # Add another purely beneficial effect
    beneficial_effect = StatEffect(
        name="pure_buff",
        stat_modifiers={
            "crit_rate": 0.2,    # +20% crit rate - beneficial
            "vitality": 0.5,     # +0.5 vitality - beneficial
        },
        duration=5,
        source="blessing"
    )
    summoner.add_effect(beneficial_effect)

    # Set up effect manager
    from autofighter.effects import EffectManager
    summoner.effect_manager = EffectManager(summoner)

    # Create summon
    summon = await Summon.create_from_summoner(
        summoner=summoner,
        summon_type="test",
        source="test_source",
        stat_multiplier=0.5
    )

    # Verify summon inherited only the purely beneficial effect
    # The mixed effect should be rejected because it has harmful modifiers
    summon_effects = summon.get_active_effects()
    assert len(summon_effects) == 1  # Only the pure buff should be inherited

    inherited_effect = summon_effects[0]
    assert inherited_effect.name == "summon_pure_buff"
    assert inherited_effect.stat_modifiers["crit_rate"] == 0.1  # 50% of 0.2
    assert inherited_effect.stat_modifiers["vitality"] == 0.25  # 50% of 0.5
