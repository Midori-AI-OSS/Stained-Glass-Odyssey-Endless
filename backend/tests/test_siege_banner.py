import asyncio

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase
import plugins.event_bus as event_bus_module


@pytest.mark.asyncio
async def test_siege_banner_enemy_debuff():
    """Test that Siege Banner debuffs enemy DEF at battle start."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.set_base_stat("defense", 100)
    foe.hp = foe.set_base_stat("max_hp", 1000)

    award_relic(party, "siege_banner")
    await apply_relics(party)

    baseline_defense = foe.defense

    # Trigger battle start with the foe
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Foe should have reduced defense (15% reduction)
    assert foe.defense < baseline_defense


@pytest.mark.asyncio
async def test_siege_banner_kill_buff():
    """Test that party gains buffs when killing enemies."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("atk", 100)
    ally.set_base_stat("defense", 50)
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.hp = 0  # Dead foe
    foe.set_base_stat("max_hp", 1000)

    award_relic(party, "siege_banner")
    await apply_relics(party)

    await BUS.emit_async("battle_start", ally)

    baseline_atk = ally.atk
    baseline_def = ally.defense

    # Simulate kill
    await BUS.emit_async("damage_taken", foe, ally, 100, 100, 0, False, "attack", {})
    await asyncio.sleep(0)

    # Ally should have increased ATK and DEF
    assert ally.atk > baseline_atk
    assert ally.defense > baseline_def


@pytest.mark.asyncio
async def test_siege_banner_multiple_kills():
    """Test that buffs stack with multiple kills."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("atk", 100)
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    award_relic(party, "siege_banner")
    await apply_relics(party)

    await BUS.emit_async("battle_start", ally)

    # Kill first foe
    foe1 = FoeBase()
    foe1.id = "foe1"
    foe1.hp = 0
    await BUS.emit_async("damage_taken", foe1, ally, 100, 100, 0, False, "attack", {})
    await asyncio.sleep(0)

    atk_after_first_kill = ally.atk

    # Kill second foe
    foe2 = FoeBase()
    foe2.id = "foe2"
    foe2.hp = 0
    await BUS.emit_async("damage_taken", foe2, ally, 100, 100, 0, False, "attack", {})
    await asyncio.sleep(0)

    # ATK should be higher after second kill
    assert ally.atk > atk_after_first_kill


@pytest.mark.asyncio
async def test_siege_banner_multiple_stacks():
    """Test that multiple relic stacks increase enemy debuff."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.set_base_stat("defense", 100)
    foe.hp = foe.set_base_stat("max_hp", 1000)

    # Award 2 stacks
    award_relic(party, "siege_banner")
    award_relic(party, "siege_banner")
    await apply_relics(party)

    baseline_defense = foe.defense

    # Trigger battle start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # With 2 stacks, debuff should be 30% (15% * 2)
    # Defense reduction should be more significant
    assert foe.defense < baseline_defense


@pytest.mark.asyncio
async def test_siege_banner_cleanup():
    """Test that state is cleaned up on battle end."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("atk", 100)
    ally.set_base_stat("defense", 50)
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.hp = 0

    award_relic(party, "siege_banner")
    await apply_relics(party)

    await BUS.emit_async("battle_start", ally)

    baseline_atk = ally.atk
    baseline_def = ally.defense

    # Kill a foe
    await BUS.emit_async("damage_taken", foe, ally, 100, 100, 0, False, "attack", {})
    await asyncio.sleep(0)

    # Check that state exists and has kills
    state = getattr(party, "_siege_banner_state", None)
    assert state is not None
    assert state.get("kills", 0) > 0

    # Stats should be buffed
    buffed_atk = ally.atk
    buffed_def = ally.defense
    assert buffed_atk > baseline_atk
    assert buffed_def > baseline_def

    # End battle
    await BUS.emit_async("battle_end")
    await asyncio.sleep(0)

    # State should still exist but kills should be reset
    state_after = getattr(party, "_siege_banner_state", None)
    if state_after is not None:
        assert state_after.get("kills", 0) == 0
    
    # Most importantly: buffs should be removed, stats should return to baseline
    assert ally.atk == baseline_atk, f"ATK should return to baseline {baseline_atk}, but is {ally.atk}"
    assert ally.defense == baseline_def, f"DEF should return to baseline {baseline_def}, but is {ally.defense}"
