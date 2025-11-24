from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.persona_ice_cryo_cycle import PersonaIceCryoCycle

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PersonaIceCryoCycleGlitched(PersonaIceCryoCycle):
    """[GLITCHED] Persona Ice's Cryo Cycle - doubled freeze duration and chill stacks.

    This glitched variant doubles the effectiveness of freeze mechanics and
    chill stacking, making Ice Persona an even more dominant crowd controller.
    """
    plugin_type = "passive"
    id = "persona_ice_cryo_cycle_glitched"
    name = "Glitched Cryo Cycle"
    trigger = "action_taken"
    max_stacks = 5
    stack_display = "number"

    async def apply(self, target: "Stats", **_: object) -> None:
        """Add frost layer with DOUBLED healing."""
        entity_id = id(target)
        current_layers = self._frost_layers.get(entity_id, 0) + 1
        current_layers = min(current_layers, self.max_stacks)
        self._frost_layers[entity_id] = current_layers

        # DOUBLED: 1% max HP per action instead of 0.5%
        base_heal = max(1, int(target.max_hp * 0.010))  # Was 0.005
        pending_total = self._pending_heal.get(entity_id, 0) + base_heal
        # DOUBLED: 10% max HP cap instead of 5%
        heal_cap = max(1, int(target.max_hp * 0.10))  # Was 0.05
        self._pending_heal[entity_id] = min(pending_total, heal_cap)

        self._apply_frost_shell(target, current_layers)

    async def on_turn_end(self, target: "Stats") -> None:
        """Apply DOUBLED frost bonuses."""
        entity_id = id(target)
        pending = self._pending_heal.get(entity_id, 0)
        layers = self._frost_layers.get(entity_id, 0)

        if pending > 0:
            await target.apply_healing(
                pending,
                healer=target,
                source_type="passive",
                source_name=self.id,
            )
            self._pending_heal[entity_id] = 0

        if layers <= 0:
            self._clear_frost_shell(target)
            return

        # DOUBLED: 2% mitigation per layer instead of 1%
        barrier_bonus = layers * 0.02  # Was 0.01
        target.remove_effect_by_name(f"{self.id}_frost_barrier")
        barrier = StatEffect(
            name=f"{self.id}_frost_barrier",
            stat_modifiers={"mitigation": barrier_bonus},
            duration=1,
            source=self.id,
        )
        target.add_effect(barrier)

        new_layers = max(layers - 1, 0)
        self._frost_layers[entity_id] = new_layers

    def _apply_frost_shell(self, target: "Stats", layers: int) -> None:
        """Apply DOUBLED frost shell bonuses."""
        # DOUBLED: 4% mitigation per layer instead of 2%
        mitigation_bonus = layers * 0.04  # Was 0.02
        target.remove_effect_by_name(f"{self.id}_frost_shell")
        shell = StatEffect(
            name=f"{self.id}_frost_shell",
            stat_modifiers={"mitigation": mitigation_bonus},
            duration=-1,
            source=self.id,
        )
        target.add_effect(shell)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Ice attacks apply chill stacks (doubled). "
            "High chill causes freeze (doubled duration). "
            "Frozen enemies take doubled damage from Ice attacks."
        )
