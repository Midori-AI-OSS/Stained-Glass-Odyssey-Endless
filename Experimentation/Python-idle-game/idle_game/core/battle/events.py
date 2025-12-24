"""Battle event system for combat triggers.

Ported from backend/autofighter/rooms/battle/events.py
Simplified for Qt-based idle game (synchronous, minimal plugin system).
"""

from typing import Any

from ..stats import Stats
from ..stats import set_enrage_percent


def handle_battle_start(
    foes: list[Stats],
    party_members: list[Stats],
) -> None:
    """Emit battle start events for all combatants.

    In full implementation, this would trigger:
    - Plugin passive effects
    - Relic battle start effects
    - Card battle start hooks

    Currently stubbed for initial combat engine integration.
    """
    # Reset enrage at battle start
    set_enrage_percent(0.0)

    # Trigger battle_start for all foes
    for foe in foes:
        # TODO: Emit to plugin event system when available
        # For now, just ensure foe is properly initialized
        if not hasattr(foe, "action_points"):
            foe.action_points = getattr(foe, "actions_per_turn", 1)

    # Trigger battle_start for all party members
    for member in party_members:
        # TODO: Emit to plugin event system when available
        if not hasattr(member, "action_points"):
            member.action_points = getattr(member, "actions_per_turn", 1)


def handle_battle_end(
    foes: list[Stats],
    party_members: list[Stats],
) -> None:
    """Emit defeat and battle end events for combatants.

    In full implementation, this would trigger:
    - Entity defeat events
    - Battle end cleanup
    - Effect expiration
    - Stat resets

    Currently stubbed for initial combat engine integration.
    """
    # Emit defeat events for dead combatants
    for foe in foes:
        if foe.hp <= 0:
            # TODO: Emit entity_defeat event when plugin system available
            pass

    for member in party_members:
        if member.hp <= 0:
            # TODO: Emit entity_defeat event when plugin system available
            pass

    # Reset enrage at battle end
    set_enrage_percent(0.0)


def handle_entity_death(entity: Stats, context: Any = None) -> None:
    """Handle entity death during combat.

    Args:
        entity: The Stats object that died
        context: Optional battle context for additional processing
    """
    # Mark entity as dead
    if entity.hp > 0:
        entity.hp = 0

    # TODO: Trigger on_death effects when plugin system available
    # TODO: Check for revival effects
    # TODO: Credit kill to appropriate party member


def handle_damage_dealt(
    attacker: Stats,
    target: Stats,
    damage: int,
    damage_type: str = "Generic",
    context: Any = None,
) -> None:
    """Handle damage dealt event.

    Args:
        attacker: Stats object that dealt damage
        target: Stats object that received damage
        damage: Amount of damage dealt
        damage_type: Type of damage (for element tracking)
        context: Optional battle context
    """
    # Update damage tracking
    if hasattr(attacker, "damage_dealt_total"):
        attacker.damage_dealt_total += damage
    if hasattr(target, "damage_taken_total"):
        target.damage_taken_total += damage
        target.last_damage_taken = damage

    # TODO: Trigger on_damage_dealt effects when plugin system available
    # TODO: Trigger on_damage_taken effects
    # TODO: Update combat log


def handle_healing(
    healer: Stats,
    target: Stats,
    healing: int,
    context: Any = None,
) -> None:
    """Handle healing event.

    Args:
        healer: Stats object that provided healing
        target: Stats object that received healing
        healing: Amount of healing provided
        context: Optional battle context
    """
    # Apply healing with overheal check
    old_hp = target.hp
    max_hp = target.max_hp

    if target.overheal_enabled:
        # Allow overheal (becomes shields)
        target.hp += healing
        if target.hp > max_hp:
            overheal = target.hp - max_hp
            target.hp = max_hp
            target.shields += overheal
    else:
        # Cap at max HP
        target.hp = min(target.hp + healing, max_hp)

    actual_healing = target.hp - old_hp

    # TODO: Trigger on_heal effects when plugin system available
    # TODO: Update combat log


def handle_shield_applied(
    source: Stats,
    target: Stats,
    shield_amount: int,
    context: Any = None,
) -> None:
    """Handle shield application.

    Args:
        source: Stats object that applied the shield
        target: Stats object that received the shield
        shield_amount: Amount of shield applied
        context: Optional battle context
    """
    if hasattr(target, "shields"):
        target.shields += shield_amount
    else:
        target.shields = shield_amount

    # TODO: Trigger on_shield effects when plugin system available
    # TODO: Update combat log


def handle_effect_applied(
    source: Stats,
    target: Stats,
    effect_type: str,
    effect_data: dict[str, Any],
    context: Any = None,
) -> None:
    """Handle effect application (buffs/debuffs).

    Args:
        source: Stats object that applied the effect
        target: Stats object that received the effect
        effect_type: Type of effect applied
        effect_data: Effect parameters
        context: Optional battle context
    """
    # TODO: Apply effect through effect manager
    # TODO: Trigger effect application hooks
    # TODO: Update combat log
    pass


# Event handler registry for future plugin system integration
_EVENT_HANDLERS: dict[str, list] = {
    "battle_start": [],
    "battle_end": [],
    "entity_death": [],
    "damage_dealt": [],
    "healing": [],
    "shield_applied": [],
    "effect_applied": [],
}


def register_event_handler(event_type: str, handler: Any) -> None:
    """Register a custom event handler.

    Args:
        event_type: Type of event to handle
        handler: Callable to invoke when event occurs
    """
    if event_type in _EVENT_HANDLERS:
        if handler not in _EVENT_HANDLERS[event_type]:
            _EVENT_HANDLERS[event_type].append(handler)


def clear_event_handlers() -> None:
    """Clear all registered event handlers."""
    for handlers in _EVENT_HANDLERS.values():
        handlers.clear()
