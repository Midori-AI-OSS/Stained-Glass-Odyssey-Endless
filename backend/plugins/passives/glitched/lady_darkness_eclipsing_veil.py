from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.lady_darkness_eclipsing_veil import LadyDarknessEclipsingVeil

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyDarknessEclipsingVeilGlitched(LadyDarknessEclipsingVeil):
    """[GLITCHED] Lady Darkness's Eclipsing Veil - doubled DoT siphoning.

    This glitched variant doubles the healing from DoT ticks (2% instead of 1%)
    while maintaining the same DoT extension and debuff resistance mechanics,
    resulting in much stronger sustain from battlefield DoT damage.
    """
    plugin_type = "passive"
    id = "lady_darkness_eclipsing_veil_glitched"
    name = "Glitched Eclipsing Veil"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    async def on_dot_tick(self, target: "Stats", dot_damage: int) -> None:
        """Siphon DOUBLED 2% of DoT damage as HoT (was 1%)."""
        # DOUBLED siphon (2% instead of 1%)
        siphoned_healing = max(1, int(dot_damage * 0.02))  # Doubled from 0.01

        # Apply immediate healing
        await target.apply_healing(siphoned_healing)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Extends DoTs by one turn and siphons 2% of each DoT tick (doubled) as healing. "
            "Resisting a debuff grants +5% attack, stacking indefinitely."
        )
