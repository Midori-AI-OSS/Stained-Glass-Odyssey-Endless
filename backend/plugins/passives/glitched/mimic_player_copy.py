from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.mimic_player_copy import MimicPlayerCopy

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class MimicPlayerCopyGlitched(MimicPlayerCopy):
    """[GLITCHED] Mimic Player Copy - doubled copy effectiveness.

    This glitched variant doubles the stat copying percentage and ability
    effectiveness when mimicking player characters, creating superior copies.
    """
    plugin_type = "passive"
    id = "mimic_player_copy_glitched"
    name = "Glitched Player Copy"
    trigger = "battle_start"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats", **kwargs) -> None:
        """Apply copied stats with DOUBLED effectiveness (50% debuff instead of 25%)."""
        from autofighter.stats import BUS

        participants = kwargs.get('participants', [])
        if not participants:
            return

        player_stats = self._find_player_stats(participants)
        if player_stats:
            self._copy_player_stats(target, player_stats)

        entity_id = id(target)
        self._target_id = entity_id

        def effect_listener(effect_name, entity, details=None):
            self._on_effect_applied(effect_name, entity, details)

        BUS.subscribe("effect_applied", effect_listener)

        def _on_battle_end(entity) -> None:
            BUS.unsubscribe("effect_applied", effect_listener)
            BUS.unsubscribe("battle_end", _on_battle_end)

        BUS.subscribe("battle_end", _on_battle_end)

        copied_stats = self._copied_stats.get(entity_id, {})

        # DOUBLED effectiveness: 50% debuff instead of 25%
        # This means keeping 50% of stats instead of 75%
        for stat_name, original_value in copied_stats.items():
            debuffed_value = int(original_value * 0.50)  # Was 0.75 (25% reduction), now 0.50 (50% reduction gives 2x)

            copy_effect = StatEffect(
                name=f"{self.id}_copied_{stat_name}",
                stat_modifiers={stat_name: debuffed_value - getattr(target, stat_name)},
                duration=-1,
                source=self.id,
            )
            target.add_effect(copy_effect)

        if entity_id in self._copied_passive:
            await self._apply_copied_passive(target)

    async def _apply_copied_passive(self, target: "Stats") -> None:
        """Apply copied passive at DOUBLED strength."""
        entity_id = id(target)
        passive_id = self._copied_passive[entity_id]

        if passive_id == "player_level_up_bonus":
            # DOUBLED: 0.35 bonus instead of 0.175 (full strength instead of half)
            level_bonus_effect = StatEffect(
                name=f"{self.id}_copied_level_bonus",
                stat_modifiers={"exp_multiplier": 0.35},  # Was 0.175
                duration=-1,
                source=self.id,
            )
            target.add_effect(level_bonus_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Copies a player character with doubled stat percentage (100% effectiveness). "
            "Inherits doubled ability power and passive effects. "
            "Maintains the copied identity throughout battle."
        )
