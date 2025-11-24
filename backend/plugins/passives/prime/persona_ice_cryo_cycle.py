from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.persona_ice_cryo_cycle import PersonaIceCryoCycle

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PersonaIceCryoCyclePrime(PersonaIceCryoCycle):
    """[PRIME] Cryo Cycle with thicker frost and higher heals."""

    plugin_type = "passive"
    id = "persona_ice_cryo_cycle_prime"
    name = "Prime Cryo Cycle"
    trigger = "action_taken"
    max_stacks = 8
    stack_display = "number"

    async def apply(self, target: "Stats", **_: object) -> None:
        entity_id = id(target)
        current_layers = min(self._frost_layers.get(entity_id, 0) + 1, self.max_stacks)
        self._frost_layers[entity_id] = current_layers

        base_heal = max(1, int(target.max_hp * 0.01))
        pending_total = self._pending_heal.get(entity_id, 0) + base_heal
        heal_cap = max(1, int(target.max_hp * 0.08))
        self._pending_heal[entity_id] = min(pending_total, heal_cap)

        self._apply_frost_shell(target, current_layers)

    async def on_turn_end(self, target: "Stats") -> None:
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

        barrier_bonus = layers * 0.015
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
        target.remove_effect_by_name(f"{self.id}_frost_shell")
        if layers <= 0:
            return

        mitigation_bonus = layers * 0.03
        regain_bonus = layers * 10
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

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Stores up to eight Frost Layers, healing 1% max HP per action (capped at 8%). "
            "Each layer adds 3% mitigation and +10 regain with sturdier end-of-turn barriers."
        )

