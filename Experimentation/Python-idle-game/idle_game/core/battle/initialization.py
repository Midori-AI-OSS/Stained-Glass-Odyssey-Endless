"""Battle initialization and context setup.

Ported from backend/autofighter/rooms/battle/turn_loop/initialization.py
for Qt-based idle game (synchronous).
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable
from typing import Optional

from ..action_queue import ActionQueue
from ..effect_manager import EffectManager
from ..stats import Stats


@dataclass
class EnrageState:
    """Tracks enrage state during battle."""

    threshold: int = 100
    current: int = 0

    def increment(self, amount: int = 1) -> None:
        """Increase enrage counter."""
        self.current += amount

    def is_enraged(self) -> bool:
        """Check if battle is in enrage state."""
        return self.current >= self.threshold

    def get_percent(self) -> float:
        """Get enrage percentage (0.0 to 1.0+)."""
        if self.threshold <= 0:
            return 0.0
        return self.current / self.threshold


@dataclass
class TurnLoopContext:
    """Shared data structure used while processing the battle turn loop.

    Stores all battle state including combatants, effects, and tracking data.
    Adapted from async version to synchronous execution.
    """

    # Core references
    party_members: list[Stats] = field(default_factory=list)
    foes: list[Stats] = field(default_factory=list)

    # Effect management
    party_effects: list[EffectManager] = field(default_factory=list)
    foe_effects: list[EffectManager] = field(default_factory=list)

    # Battle state
    enrage_state: EnrageState = field(default_factory=EnrageState)
    action_queue: ActionQueue | None = None

    # Turn tracking
    turn: int = 0
    action_turn: int = 0

    # Rewards and progression
    exp_reward: int = 0
    gold_reward: int = 0
    temp_rdr: float = 1.0  # Rare drop rate multiplier

    # Death tracking
    credited_foe_ids: set[str] = field(default_factory=set)
    credited_party_ids: set[str] = field(default_factory=set)

    # Optional callbacks for UI updates
    on_progress: Optional[Callable[[dict[str, Any]], None]] = None

    @property
    def all_combatants(self) -> list[Stats]:
        """Return all combatants (party + foes)."""
        return self.party_members + self.foes

    def is_battle_over(self) -> bool:
        """Check if battle has ended (victory or defeat)."""
        party_alive = any(member.hp > 0 for member in self.party_members)
        foes_alive = any(foe.hp > 0 for foe in self.foes)
        return not party_alive or not foes_alive

    def is_victory(self) -> bool:
        """Check if party won the battle."""
        if not self.is_battle_over():
            return False
        party_alive = any(member.hp > 0 for member in self.party_members)
        foes_alive = any(foe.hp > 0 for foe in self.foes)
        return party_alive and not foes_alive

    def is_defeat(self) -> bool:
        """Check if party lost the battle."""
        if not self.is_battle_over():
            return False
        party_alive = any(member.hp > 0 for member in self.party_members)
        return not party_alive


def initialize_turn_loop(
    *,
    party_members: list[Stats],
    foes: list[Stats],
    party_effects: list[EffectManager] | None = None,
    foe_effects: list[EffectManager] | None = None,
    enrage_threshold: int = 100,
    temp_rdr: float = 1.0,
    on_progress: Optional[Callable[[dict[str, Any]], None]] = None,
) -> TurnLoopContext:
    """Prepare the turn loop context for battle execution.

    Args:
        party_members: List of player Stats objects
        foes: List of enemy Stats objects
        party_effects: Optional effect managers for party (auto-created if None)
        foe_effects: Optional effect managers for foes (auto-created if None)
        enrage_threshold: Number of turns before enrage triggers
        temp_rdr: Temporary rare drop rate multiplier
        on_progress: Optional callback for battle progress updates

    Returns:
        TurnLoopContext ready for battle execution
    """
    # Create effect managers if not provided
    if party_effects is None:
        party_effects = [EffectManager(member) for member in party_members]
    if foe_effects is None:
        foe_effects = [EffectManager(foe) for foe in foes]

    # Create enrage state
    enrage_state = EnrageState(threshold=enrage_threshold)

    # Create action queue with all combatants
    all_combatants = party_members + foes
    action_queue = ActionQueue(combatants=all_combatants.copy())

    # Build context
    context = TurnLoopContext(
        party_members=party_members,
        foes=foes,
        party_effects=party_effects,
        foe_effects=foe_effects,
        enrage_state=enrage_state,
        action_queue=action_queue,
        temp_rdr=temp_rdr,
        on_progress=on_progress,
    )

    # Emit initial progress if callback provided
    if on_progress:
        try:
            on_progress(
                {
                    "phase": "initialization",
                    "turn": 0,
                    "party_hp": [m.hp for m in party_members],
                    "foe_hp": [f.hp for f in foes],
                }
            )
        except Exception:
            pass

    return context
