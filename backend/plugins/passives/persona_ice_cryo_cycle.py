from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PersonaIceCryoCycle:
    """PersonaIce passive that builds frost layers to sustain the party."""

    plugin_type = "passive"
    id = "persona_ice_cryo_cycle"
    name = "Cryo Cycle"
    trigger = "action_taken"
    max_stacks = 5
    stack_display = "number"

    _frost_layers: ClassVar[dict[int, int]] = {}
    _pending_heal: ClassVar[dict[int, int]] = {}

    async def apply(self, target: "Stats", **_: object) -> None:
        """Add a frost layer whenever PersonaIce acts."""

        entity_id = id(target)
        current_layers = self._frost_layers.get(entity_id, 0) + 1
        current_layers = min(current_layers, self.max_stacks)
        self._frost_layers[entity_id] = current_layers

        base_heal = max(1, int(target.max_hp * 0.005))
        pending_total = self._pending_heal.get(entity_id, 0) + base_heal
        heal_cap = max(1, int(target.max_hp * 0.05))
        self._pending_heal[entity_id] = min(pending_total, heal_cap)

        self._apply_frost_shell(target, current_layers)

    async def on_turn_end(self, target: "Stats") -> None:
        """Convert stored chill into mitigation and healing at turn end."""

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

        barrier_bonus = layers * 0.01
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
        self._apply_frost_shell(target, new_layers)

    def _apply_frost_shell(self, target: "Stats", layers: int) -> None:
        """Refresh the persistent frost shell mitigation effect."""

        target.remove_effect_by_name(f"{self.id}_frost_shell")
        if layers <= 0:
            return

        mitigation_bonus = layers * 0.02
        regain_bonus = layers * 8
        shell = StatEffect(
            name=f"{self.id}_frost_shell",
            stat_modifiers={
                "mitigation": mitigation_bonus,
                "regain": regain_bonus,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(shell)

    def _clear_frost_shell(self, target: "Stats") -> None:
        """Remove frost shell effects when no layers remain."""

        target.remove_effect_by_name(f"{self.id}_frost_shell")
        target.remove_effect_by_name(f"{self.id}_frost_barrier")

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Expose frost layer count for UI."""

        return cls._frost_layers.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Actions add Frost Layers (up to five), granting 2% mitigation and +8 regain per layer. "
            "Turn end healing releases stored chill for up to 5% max HP and applies a 1-turn barrier "
            "before a layer melts."
        )
