from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stats import BUS
from autofighter.stats import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class MimicPlayerCopy:
    """Mimic's passive - copies player stats and passive at half strength."""

    plugin_type = "passive"
    id = "mimic_player_copy"
    name = "Player Copy"
    trigger = "battle_start"  # Triggers at start of battle to copy player
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of copied stats and passives
    _copied_stats: ClassVar[dict[int, dict]] = {}  # entity_id -> copied_stats
    _copied_passive: ClassVar[dict[int, str]] = {}  # entity_id -> passive_id
    _instances: ClassVar[dict[int, "MimicPlayerCopy"]] = {}

    def __post_init__(self) -> None:
        self._target_id: int | None = None

    async def apply(self, target: "Stats", party: list | None = None) -> None:
        """Apply Mimic's player copying mechanics."""
        entity_id = id(target)
        self.__class__._instances[entity_id] = self
        self._target_id = entity_id

        # Initialize tracking if not present
        if entity_id not in self._copied_stats:
            player_stats = self._find_player_stats(party or [])
            if player_stats:
                self._copy_player_stats(target, player_stats)

        # Remove any external buffs to prevent stacking beyond copied effects
        for effect in target.get_active_effects():
            if not effect.name.startswith(f"{self.id}_"):
                target.remove_effect_by_name(effect.name)

        # Subscribe to effect application events to block future buffs
        BUS.subscribe("effect_applied", self._on_effect_applied)

        # Apply 25% debuff to all copied stats
        copied_stats = self._copied_stats.get(entity_id, {})

        # Apply copied stats with 25% reduction
        for stat_name, original_value in copied_stats.items():
            debuffed_value = int(original_value * 0.75)  # 25% debuff

            copy_effect = StatEffect(
                name=f"{self.id}_copied_{stat_name}",
                stat_modifiers={stat_name: debuffed_value - getattr(target, stat_name)},
                duration=-1,  # Permanent
                source=self.id,
            )
            target.add_effect(copy_effect)

        # Apply copied passive at half strength if present
        if entity_id in self._copied_passive:
            await self._apply_copied_passive(target)

    def _find_player_stats(self, participants: list) -> dict:
        """Locate the player entity in the provided participants and return its stats."""
        for entity in participants:
            if getattr(entity, "id", None) == "player":
                return {
                    "max_hp": entity.max_hp,
                    "atk": entity.atk,
                    "defense": entity.defense,
                    "mitigation": getattr(entity, "mitigation", 0),
                }
        return {}

    def _copy_player_stats(self, target: "Stats", player_stats: dict) -> None:
        """Copy player stats to Mimic."""
        entity_id = id(target)
        self._copied_stats[entity_id] = player_stats.copy()

        # Also copy player's passive if they have one
        # Simplified - assume player has "player_level_up_bonus" passive
        player_passive = "player_level_up_bonus"
        if player_passive:
            self._copied_passive[entity_id] = player_passive

    async def _apply_copied_passive(self, target: "Stats") -> None:
        """Apply copied passive at half strength."""
        entity_id = id(target)
        passive_id = self._copied_passive[entity_id]

        # Create a weakened version of the player's passive
        # This would normally require dynamically loading and modifying the passive
        # For now, apply a generic half-strength effect

        if passive_id == "player_level_up_bonus":
            # Player normally gets 1.35x level up bonus, Mimic gets 1.175x (halfway to 1.0)
            level_bonus_effect = StatEffect(
                name=f"{self.id}_copied_level_bonus",
                stat_modifiers={"exp_multiplier": 0.175},  # Half of 0.35 bonus
                duration=-1,  # Permanent
                source=self.id,
            )
            target.add_effect(level_bonus_effect)

    def _on_effect_applied(
        self, effect_name: str, entity, details: dict | None = None
    ) -> None:
        """Remove only positive stat buffs applied to the Mimic."""
        if self._target_id is None or id(entity) != self._target_id:
            return

        if details and details.get("effect_type") == "stat_modifier":
            if effect_name.startswith(f"{self.id}_"):
                return

            deltas = details.get("deltas", {}) or {}
            multipliers = details.get("multipliers", {}) or {}

            is_buff = any(delta > 0 for delta in deltas.values()) or any(
                mult > 1 for mult in multipliers.values()
            )

            if is_buff:
                entity.remove_effect_by_name(effect_name)

    async def on_battle_start(self, target: "Stats", battle_participants: list) -> None:
        """Copy player stats and passive when battle starts."""
        player_stats = self._find_player_stats(battle_participants)
        if player_stats:
            entity_id = id(target)
            self._copied_stats[entity_id] = player_stats

            # Copy player's first passive if available
            player_entity = next(
                (p for p in battle_participants if getattr(p, "id", None) == "player"),
                None,
            )
            if player_entity and getattr(player_entity, "passives", None):
                self._copied_passive[entity_id] = player_entity.passives[0]

        # Remove any non-mimic effects to maintain stat parity
        for effect in target.get_active_effects():
            if not effect.name.startswith(f"{self.id}_"):
                target.remove_effect_by_name(effect.name)

    @classmethod
    def get_copied_stats(cls, target: "Stats") -> dict:
        """Get the stats copied from player."""
        return cls._copied_stats.get(id(target), {})

    @classmethod
    def get_copied_passive(cls, target: "Stats") -> str:
        """Get the passive copied from player."""
        return cls._copied_passive.get(id(target), None)

    @classmethod
    def get_description(cls) -> str:
        return "Copies the player's stats at battle start with a 25% reduction and copies the player's passive at half strength while blocking other buffs."
