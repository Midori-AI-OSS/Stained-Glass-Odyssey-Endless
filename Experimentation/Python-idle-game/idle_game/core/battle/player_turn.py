"""Player turn execution for combat.

Ported from backend/autofighter/rooms/battle/turn_loop/player_turn.py
Simplified for Qt-based idle game (synchronous, basic AI for now).
"""

import random

from ..stats import Stats
from .events import handle_damage_dealt
from .events import handle_entity_death
from .events import handle_healing
from .initialization import TurnLoopContext


def execute_player_turn(context: TurnLoopContext, actor: Stats) -> bool:
    """Execute a single player turn.

    Args:
        context: Battle context with current state
        actor: The party member taking their turn

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
    _execute_basic_attack(context, actor)

    # Decrement action points
    actor.action_points -= 1

    # Check for battle end
    if context.is_battle_over():
        return False

    # Continue if actor has more actions
    return True


def _execute_basic_attack(context: TurnLoopContext, attacker: Stats) -> None:
    """Execute a basic attack action.

    Args:
        context: Battle context
        attacker: Stats object performing the attack
    """
    # Select target (first alive foe with aggro weighting)
    target = _select_target(context.foes)
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
        # Credit the kill
        target_id = getattr(target, "id", str(id(target)))
        context.credited_foe_ids.add(target_id)


def _select_target(foes: list[Stats]) -> Stats | None:
    """Select a target from available foes using aggro weighting.

    Args:
        foes: List of enemy Stats objects

    Returns:
        Selected target or None if no valid targets
    """
    # Filter alive foes
    alive_foes = [f for f in foes if f.hp > 0]
    if not alive_foes:
        return None

    # Use aggro weighting for target selection
    weights = []
    for foe in alive_foes:
        base_aggro = getattr(foe, "base_aggro", 0.1)
        aggro_mod = getattr(foe, "aggro_modifier", 0.0)
        weight = base_aggro + aggro_mod
        weights.append(max(weight, 0.01))  # Minimum weight

    # Weighted random selection
    total_weight = sum(weights)
    pick = random.random() * total_weight
    cumulative = 0.0
    for foe, weight in zip(alive_foes, weights):
        cumulative += weight
        if pick <= cumulative:
            return foe

    return alive_foes[0]  # Fallback to first


def _calculate_damage(attacker: Stats, target: Stats) -> int:
    """Calculate damage for an attack.

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


def execute_player_healing(context: TurnLoopContext, healer: Stats) -> bool:
    """Execute a healing action (for future support characters).

    Args:
        context: Battle context
        healer: Stats object performing healing

    Returns:
        True if battle should continue
    """
    # Select target (lowest HP party member)
    target = _select_healing_target(context.party_members)
    if target is None:
        return not context.is_battle_over()

    # Calculate healing
    heal_amount = int(healer.atk * 0.5)  # 50% of ATK as healing

    # Apply healing
    handle_healing(healer, target, heal_amount, context)

    return not context.is_battle_over()


def _select_healing_target(party: list[Stats]) -> Stats | None:
    """Select party member with lowest HP% for healing.

    Args:
        party: List of party member Stats

    Returns:
        Target for healing or None
    """
    alive_members = [m for m in party if m.hp > 0]
    if not alive_members:
        return None

    # Find member with lowest HP%
    lowest_member = min(
        alive_members,
        key=lambda m: m.hp / max(m.max_hp, 1),
    )

    return lowest_member
