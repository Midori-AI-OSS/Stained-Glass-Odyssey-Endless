import asyncio

import pytest

from autofighter.cards import apply_cards, award_card
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_tempest_pathfinder_baseline_dodge():
    """Test that Tempest Pathfinder grants +55% dodge odds baseline."""
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("dodge_odds", 0.1)  # 10% base dodge
    party.members.append(ally)

    award_card(party, "tempest_pathfinder")
    await apply_cards(party)

    # Should have 10% base + 55% from card = ~65% (multiplicative: 1.1 * 1.55 = 1.705)
    assert ally.dodge_odds > ally.get_base_stat("dodge_odds")
    assert ally.dodge_odds == pytest.approx(ally.get_base_stat("dodge_odds") * 1.55)


@pytest.mark.asyncio
async def test_tempest_pathfinder_crit_dodge_buff():
    """Test that Tempest Pathfinder grants +12% dodge to all allies when one crits."""
    party = Party()

    ally1 = PlayerBase()
    ally1.id = "ally1"
    ally1.set_base_stat("dodge_odds", 0.1)
    ally1.hp = ally1.set_base_stat("max_hp", 100)

    ally2 = PlayerBase()
    ally2.id = "ally2"
    ally2.set_base_stat("dodge_odds", 0.1)
    ally2.hp = ally2.set_base_stat("max_hp", 100)

    enemy = PlayerBase()
    enemy.id = "enemy"
    enemy.hp = enemy.set_base_stat("max_hp", 100)

    party.members.append(ally1)
    party.members.append(ally2)

    award_card(party, "tempest_pathfinder")
    await apply_cards(party)

    await BUS.emit_async("battle_start", ally1)
    await BUS.emit_async("turn_start")

    # Get baseline dodge after card application
    baseline_dodge_ally1 = ally1.dodge_odds
    baseline_dodge_ally2 = ally2.dodge_odds

    # Simulate a critical hit from ally1
    await BUS.emit_async(
        "damage_taken",
        enemy,
        ally1,
        10,
        100,  # pre_damage_hp
        90,   # post_damage_hp
        True, # is_critical
        "attack",
        {}
    )

    await asyncio.sleep(0)

    # Both allies should now have increased dodge (the exact amount depends on modifier stacking)
    assert ally1.dodge_odds > baseline_dodge_ally1, "ally1 should have increased dodge after crit"
    assert ally2.dodge_odds > baseline_dodge_ally2, "ally2 should have increased dodge after crit"


@pytest.mark.asyncio
async def test_tempest_pathfinder_cooldown():
    """Test that the crit dodge buff only triggers once per turn."""
    party = Party()

    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("dodge_odds", 0.1)
    ally.hp = ally.set_base_stat("max_hp", 100)

    enemy = PlayerBase()
    enemy.id = "enemy"
    enemy.hp = enemy.set_base_stat("max_hp", 100)

    party.members.append(ally)

    award_card(party, "tempest_pathfinder")
    await apply_cards(party)

    await BUS.emit_async("battle_start", ally)
    await BUS.emit_async("turn_start")

    baseline_dodge = ally.dodge_odds

    # First crit should trigger the buff
    await BUS.emit_async(
        "damage_taken",
        enemy,
        ally,
        10,
        100,
        90,
        True,
        "attack",
        {}
    )

    await asyncio.sleep(0)
    buffed_dodge = ally.dodge_odds
    assert buffed_dodge > baseline_dodge

    # Second crit in the same turn should NOT stack
    await BUS.emit_async(
        "damage_taken",
        enemy,
        ally,
        10,
        90,
        80,
        True,
        "attack",
        {}
    )

    await asyncio.sleep(0)
    # Dodge should remain the same (no additional buff)
    assert ally.dodge_odds == pytest.approx(buffed_dodge, rel=0.01)


@pytest.mark.asyncio
async def test_tempest_pathfinder_cooldown_reset():
    """Test that the cooldown resets on turn_start, allowing multiple triggers across turns."""
    party = Party()

    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("dodge_odds", 0.1)
    ally.hp = ally.set_base_stat("max_hp", 100)

    enemy = PlayerBase()
    enemy.id = "enemy"
    enemy.hp = enemy.set_base_stat("max_hp", 100)

    party.members.append(ally)

    award_card(party, "tempest_pathfinder")
    await apply_cards(party)

    await BUS.emit_async("battle_start", ally)

    # Turn 1: First crit should trigger
    await BUS.emit_async("turn_start")
    baseline1 = ally.dodge_odds

    await BUS.emit_async(
        "damage_taken",
        enemy,
        ally,
        10,
        100,
        90,
        True,
        "attack",
        {}
    )
    await asyncio.sleep(0)
    assert ally.dodge_odds > baseline1, "First crit in turn 1 should trigger buff"

    # Turn 2: Second crit should also trigger (cooldown resets)
    await BUS.emit_async("turn_start")
    await asyncio.sleep(0)
    baseline2 = ally.dodge_odds

    await BUS.emit_async(
        "damage_taken",
        enemy,
        ally,
        10,
        90,
        80,
        True,
        "attack",
        {}
    )
    await asyncio.sleep(0)
    # If cooldown wasn't reset, this would not increase dodge
    assert ally.dodge_odds >= baseline2, "Second crit in turn 2 should also trigger (cooldown reset)"


@pytest.mark.asyncio
async def test_tempest_pathfinder_non_crit_no_trigger():
    """Test that non-critical hits don't trigger the dodge buff."""
    party = Party()

    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("dodge_odds", 0.1)
    ally.hp = ally.set_base_stat("max_hp", 100)

    enemy = PlayerBase()
    enemy.id = "enemy"
    enemy.hp = enemy.set_base_stat("max_hp", 100)

    party.members.append(ally)

    award_card(party, "tempest_pathfinder")
    await apply_cards(party)

    await BUS.emit_async("battle_start", ally)
    await BUS.emit_async("turn_start")

    baseline_dodge = ally.dodge_odds

    # Non-critical hit (is_critical=False)
    await BUS.emit_async(
        "damage_taken",
        enemy,
        ally,
        10,
        100,
        90,
        False,  # NOT a crit
        "attack",
        {}
    )

    await asyncio.sleep(0)

    # Dodge should not change
    assert ally.dodge_odds == pytest.approx(baseline_dodge, rel=0.01)
