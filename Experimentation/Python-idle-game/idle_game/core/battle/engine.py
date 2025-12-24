"""Battle engine handling turn processing and rewards.

Ported from backend/autofighter/rooms/battle/engine.py
Simplified for Qt-based idle game (synchronous execution).
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from ..stats import Stats
from ..stats import set_enrage_percent
from .events import handle_battle_end
from .events import handle_battle_start
from .foe_turn import execute_foe_turn
from .initialization import TurnLoopContext
from .initialization import initialize_turn_loop
from .player_turn import execute_player_turn
from .resolution import calculate_battle_rewards


@dataclass
class BattleResult:
    """Container for battle outcome and rewards.

    Attributes:
        victory: Whether the party won
        turns_taken: Number of turns in the battle
        gold: Gold reward
        exp: Experience reward
        cards: List of card drops
        relics: List of relic drops
        items: List of item drops
        party_survivors: IDs of surviving party members
        final_party_hp: Final HP values of party members
    """

    victory: bool = False
    turns_taken: int = 0
    gold: int = 0
    exp: int = 0
    cards: list[dict[str, Any]] = field(default_factory=list)
    relics: list[dict[str, Any]] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    party_survivors: list[str] = field(default_factory=list)
    final_party_hp: list[int] = field(default_factory=list)


def run_battle(
    party_members: list[Stats],
    foes: list[Stats],
    enrage_threshold: int = 100,
    temp_rdr: float = 1.0,
    max_turns: int = 1000,
) -> BattleResult:
    """Execute the main battle loop and return the result.

    Args:
        party_members: List of player Stats objects
        foes: List of enemy Stats objects
        enrage_threshold: Number of turns before enrage triggers
        temp_rdr: Temporary rare drop rate multiplier
        max_turns: Maximum turns before forced draw

    Returns:
        BattleResult with battle outcome and rewards
    """
    # Initialize battle context
    context = initialize_turn_loop(
        party_members=party_members,
        foes=foes,
        enrage_threshold=enrage_threshold,
        temp_rdr=temp_rdr,
    )

    # Trigger battle start events
    handle_battle_start(foes, party_members)

    # Reset enrage
    set_enrage_percent(0.0)

    # Main battle loop
    turn_count = 0
    while not context.is_battle_over() and turn_count < max_turns:
        turn_count += 1
        context.turn = turn_count

        # Get next actor from action queue
        if context.action_queue is None:
            break

        try:
            actor = context.action_queue.next_actor()
        except RuntimeError:
            # No valid actors (shouldn't happen)
            break

        # Determine if actor is party member or foe
        is_player = actor in context.party_members

        # Execute turn
        if is_player:
            continue_battle = execute_player_turn(context, actor)
        else:
            continue_battle = execute_foe_turn(context, actor)

        # Check if battle should end
        if not continue_battle:
            break

        # Update enrage state
        if turn_count % 10 == 0:
            context.enrage_state.increment(1)
            if context.enrage_state.is_enraged():
                enrage_pct = context.enrage_state.get_percent()
                set_enrage_percent(enrage_pct - 1.0)  # 0% at threshold, higher after

    # Trigger battle end events
    handle_battle_end(context.foes, context.party_members)

    # Determine victory/defeat
    victory = context.is_victory()

    # Calculate rewards
    rewards = calculate_battle_rewards(context, victory, temp_rdr)

    # Build result
    result = BattleResult(
        victory=victory,
        turns_taken=turn_count,
        gold=rewards.get("gold", 0),
        exp=rewards.get("exp", 0),
        cards=rewards.get("cards", []),
        relics=rewards.get("relics", []),
        items=rewards.get("items", []),
        party_survivors=[
            getattr(m, "id", str(id(m)))
            for m in context.party_members
            if m.hp > 0
        ],
        final_party_hp=[m.hp for m in context.party_members],
    )

    return result


def run_battle_step(context: TurnLoopContext) -> tuple[bool, bool]:
    """Execute a single battle step (one actor's turn).

    Useful for tick-based gameplay where battles progress incrementally.

    Args:
        context: Battle context (should be preserved between calls)

    Returns:
        Tuple of (battle_continues, battle_won)
        - battle_continues: True if battle should keep going
        - battle_won: True if party won (only valid if battle_continues is False)
    """
    if context.is_battle_over():
        return False, context.is_victory()

    # Get next actor
    if context.action_queue is None:
        return False, False

    try:
        actor = context.action_queue.next_actor()
    except RuntimeError:
        return False, False

    # Increment turn counter
    context.turn += 1

    # Determine actor type
    is_player = actor in context.party_members

    # Execute turn
    if is_player:
        continue_battle = execute_player_turn(context, actor)
    else:
        continue_battle = execute_foe_turn(context, actor)

    # Update enrage
    if context.turn % 10 == 0:
        context.enrage_state.increment(1)
        if context.enrage_state.is_enraged():
            enrage_pct = context.enrage_state.get_percent()
            set_enrage_percent(enrage_pct - 1.0)

    # Check battle state
    if not continue_battle or context.is_battle_over():
        return False, context.is_victory()

    return True, False


def finalize_battle(context: TurnLoopContext) -> BattleResult:
    """Finalize battle and calculate rewards.

    Call this after run_battle_step returns battle_continues=False.

    Args:
        context: Battle context

    Returns:
        BattleResult with outcome and rewards
    """
    # Trigger battle end events
    handle_battle_end(context.foes, context.party_members)

    # Determine victory
    victory = context.is_victory()

    # Calculate rewards
    rewards = calculate_battle_rewards(context, victory, context.temp_rdr)

    # Build result
    result = BattleResult(
        victory=victory,
        turns_taken=context.turn,
        gold=rewards.get("gold", 0),
        exp=rewards.get("exp", 0),
        cards=rewards.get("cards", []),
        relics=rewards.get("relics", []),
        items=rewards.get("items", []),
        party_survivors=[
            getattr(m, "id", str(id(m)))
            for m in context.party_members
            if m.hp > 0
        ],
        final_party_hp=[m.hp for m in context.party_members],
    )

    return result
