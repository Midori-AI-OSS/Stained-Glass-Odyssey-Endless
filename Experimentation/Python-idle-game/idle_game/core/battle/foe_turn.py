"""Foe turn execution for combat.

Ported from backend/autofighter/rooms/battle/turn_loop/foe_turn.py
Simplified for Qt-based idle game (synchronous, basic AI).
"""

import random
from typing import Any

from ..stats import Stats
from .events import handle_damage_dealt
from .events import handle_entity_death
from .initialization import TurnLoopContext


def execute_foe_turn(context: TurnLoopContext, actor: Stats) -> bool:
    """Execute a single foe turn.

    Args:
        context: Battle context with current state
        actor: The foe taking their turn

    Returns:
        True if battle should continue, False if battle is over
    """
    # Check if actor is alive
    if actor.hp <= 0:
        return not context.is_battle_over()

    # Initialize action points if needed
    if not hasattr(actor, "action_points"):
        actor.action_points = getattr(actor, "actions_per_turn", 1)

    # Reset action points if depleted
    if actor.action_points <= 0:
        actor.action_points = getattr(actor, "actions_per_turn", 1)

    # Execute action (basic attack for now)
    _execute_foe_attack(context, actor)

    # Decrement action points
    actor.action_points -= 1

    # Check for battle end
    if context.is_battle_over():
        return False

    # Continue if actor has more actions
    return True


def _execute_foe_attack(context: TurnLoopContext, attacker: Stats) -> None:
    """Execute a foe attack action.

    Args:
        context: Battle context
        attacker: Stats object performing the attack
    """
    # Select target (first alive party member with aggro weighting)
    target = _select_target(context.party_members)
    if target is None or target.hp <= 0:
        return

    # Calculate damage
    damage = _calculate_damage(attacker, target)

    # Apply damage
    actual_damage = _apply_damage(target, damage)

    # Trigger damage event
    handle_damage_dealt(
        attacker=attacker,
        target=target,
        damage=actual_damage,
        damage_type=getattr(attacker, "damage_type", "Generic"),
        context=context,
    )

    # Check if target died
    if target.hp <= 0:
        handle_entity_death(target, context)
        # Credit the kill to the foe
        target_id = getattr(target, "id", str(id(target)))
        context.credited_party_ids.add(target_id)


def _select_target(party_members: list[Stats]) -> Stats | None:
    """Select a target from party members using aggro weighting.

    Args:
        party_members: List of party member Stats objects

    Returns:
        Selected target or None if no valid targets
    """
    # Filter alive members
    alive_members = [m for m in party_members if m.hp > 0]
    if not alive_members:
        return None

    # Use aggro weighting for target selection
    weights = []
    for member in alive_members:
        base_aggro = getattr(member, "base_aggro", 0.1)
        aggro_mod = getattr(member, "aggro_modifier", 0.0)
        weight = base_aggro + aggro_mod
        weights.append(max(weight, 0.01))  # Minimum weight

    # Weighted random selection
    total_weight = sum(weights)
    pick = random.random() * total_weight
    cumulative = 0.0
    for member, weight in zip(alive_members, weights):
        cumulative += weight
        if pick <= cumulative:
            return member

    return alive_members[0]  # Fallback to first


def _calculate_damage(attacker: Stats, target: Stats) -> int:
    """Calculate damage for a foe attack.

    Args:
        attacker: Attacking Stats object
        target: Defending Stats object

    Returns:
        Damage amount
    """
    # Get attacker's ATK
    atk = attacker.atk

    # Get target's defense
    defense = target.defense

    # Base damage formula: ATK * (100 / (100 + DEF))
    damage_multiplier = 100.0 / (100.0 + max(defense, 0))
    base_damage = atk * damage_multiplier

    # Apply mitigation
    mitigation = getattr(target, "mitigation", 1.0)
    base_damage *= mitigation

    # Apply vitality (healing/damage received modifier)
    vitality = getattr(target, "vitality", 1.0)
    base_damage *= vitality

    # Check for crit
    crit_rate = getattr(attacker, "crit_rate", 0.05)
    if random.random() < crit_rate:
        crit_damage = getattr(attacker, "crit_damage", 2.0)
        base_damage *= crit_damage

    # Apply variance (±10%)
    variance = random.uniform(0.9, 1.1)
    final_damage = int(base_damage * variance)

    return max(final_damage, 1)


def _apply_damage(target: Stats, damage: int) -> int:
    """Apply damage to target, handling shields and dodge.

    Args:
        target: Stats object receiving damage
        damage: Damage amount

    Returns:
        Actual damage dealt (after shields/dodge)
    """
    # Check for dodge
    dodge_odds = getattr(target, "dodge_odds", 0.0)
    if random.random() < dodge_odds:
        return 0

    # Apply to shields first
    shields = getattr(target, "shields", 0)
    if shields > 0:
        if damage <= shields:
            target.shields = shields - damage
            target.last_shield_absorbed = damage
            return 0
        else:
            # Damage exceeds shields
            remaining_damage = damage - shields
            target.last_shield_absorbed = shields
            target.shields = 0
            damage = remaining_damage

    # Apply remaining damage to HP
    old_hp = target.hp
    target.hp = max(target.hp - damage, 0)
    actual_damage = old_hp - target.hp

    return actual_damage


def execute_foe_special_action(context: TurnLoopContext, actor: Stats) -> bool:
    """Execute a special foe action (for future foe abilities).

    Args:
        context: Battle context
        actor: Foe performing special action

    Returns:
        True if battle should continue
    """
    # Placeholder for future foe abilities
    # Could include:
    # - AoE attacks
    # - Buffs/debuffs
    # - Healing
    # - Summons
    return _execute_foe_attack(context, actor) or not context.is_battle_over()
