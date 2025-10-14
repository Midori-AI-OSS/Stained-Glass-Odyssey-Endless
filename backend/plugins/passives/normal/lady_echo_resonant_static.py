from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Optional

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyEchoResonantStatic:
    """Lady Echo's Resonant Static passive - chain lightning scaling and crit buffs."""
    plugin_type = "passive"
    id = "lady_echo_resonant_static"
    name = "Resonant Static"
    trigger = "hit_landed"  # Triggers when Lady Echo lands a hit
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of current target and consecutive hits
    _current_target: ClassVar[dict[int, int]] = {}  # entity_id -> target_id
    _consecutive_hits: ClassVar[dict[int, int]] = {}  # entity_id -> hit_count
    _party_crit_stacks: ClassVar[dict[int, int]] = {}  # entity_id -> crit_stacks

    async def apply(
        self,
        target: "Stats",
        hit_target: Optional["Stats"] = None,
        **kwargs,
    ) -> None:
        """Apply chain lightning scaling and consecutive hit tracking."""
        entity_id = id(target)

        # Initialize tracking if not present
        if entity_id not in self._consecutive_hits:
            self._consecutive_hits[entity_id] = 0
            self._party_crit_stacks[entity_id] = 0

        # Count DoTs on the hit target (enemy) for chain damage scaling
        dot_target = hit_target or target
        mgr = getattr(dot_target, "effect_manager", None)
        if mgr is not None:
            dot_count = len(getattr(mgr, "dots", []))
        else:
            dot_count = len(getattr(dot_target, "dots", []))

        chain_damage_bonus = dot_count * 0.1  # 10% per DoT

        if chain_damage_bonus > 0:
            chain_effect = StatEffect(
                name=f"{self.id}_chain_bonus",
                stat_modifiers={"atk": int(target.atk * chain_damage_bonus)},
                duration=1,  # For this attack
                source=self.id,
            )
            target.add_effect(chain_effect)

        # Apply party crit rate bonus from consecutive hits
        current_crit_stacks = self._party_crit_stacks[entity_id]
        if current_crit_stacks > 0:
            party_crit_bonus = min(current_crit_stacks * 0.02, 0.2)  # 2% per stack, max 20%

            party_crit_effect = StatEffect(
                name=f"{self.id}_party_crit",
                stat_modifiers={"crit_rate": party_crit_bonus},
                duration=-1,  # Permanent until reset
                source=self.id,
            )
            target.add_effect(party_crit_effect)

    async def on_hit_landed(
        self,
        attacker: "Stats",
        target_hit: "Stats",
        damage: int = 0,
        action_type: str = "attack",
        **_: object,
    ) -> None:
        """Track consecutive hits on the same target when an attack lands."""
        del damage, action_type  # Parameters reserved for future use

        attacker_id = id(attacker)
        target_id = id(target_hit)

        previous_target = self._current_target.get(attacker_id)
        hit_count = self._consecutive_hits.get(attacker_id, 0)
        crit_stacks = self._party_crit_stacks.get(attacker_id, 0)

        if previous_target == target_id and hit_count:
            # Consecutive hit on the same target.
            hit_count += 1
            if hit_count <= 10:
                crit_stacks = min(crit_stacks + 1, 10)
        else:
            # Target changed (or this is the first tracked hit) - reset stacks.
            hit_count = 1
            crit_stacks = 0
            attacker.remove_effect_by_name(f"{self.id}_party_crit")

        self._consecutive_hits[attacker_id] = hit_count
        self._party_crit_stacks[attacker_id] = crit_stacks
        self._current_target[attacker_id] = target_id

    @classmethod
    def get_consecutive_hits(cls, attacker: "Stats") -> int:
        """Get current consecutive hits on same target."""
        return cls._consecutive_hits.get(id(attacker), 0)

    @classmethod
    def get_party_crit_stacks(cls, attacker: "Stats") -> int:
        """Get current party crit rate stacks."""
        return cls._party_crit_stacks.get(id(attacker), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Chain lightning hits deal +10% damage per DoT on the target. "
            "Consecutive hits on the same foe grant the party +2% crit rate per stack, up to 20%."
        )
