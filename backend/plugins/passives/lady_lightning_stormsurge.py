from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightningStormsurge:
    """Lady Lightning's Stormsurge passive - accelerates tempo and overloads shocks."""

    plugin_type = "passive"
    id = "lady_lightning_stormsurge"
    name = "Stormsurge"
    trigger = ["action_taken", "hit_landed"]
    max_stacks = 1
    stack_display = "spinner"

    _tempo_stacks: ClassVar[dict[int, int]] = {}
    _shock_stacks: ClassVar[dict[tuple[int, int], int]] = {}

    async def apply(self, target: "Stats", event: str | None = None, **kwargs) -> None:
        """Ensure tempo tracking exists for the owning combatant."""

        entity_id = id(target)
        if entity_id not in self._tempo_stacks:
            self._tempo_stacks[entity_id] = 0

    async def on_action_taken(self, target: "Stats", **kwargs) -> None:
        """Build tempo stacks whenever Lady Lightning acts."""

        entity_id = id(target)
        current = self._tempo_stacks.get(entity_id, 0)
        tempo = min(current + 1, 4)
        self._tempo_stacks[entity_id] = tempo

        tempo_effect = StatEffect(
            name=f"{self.id}_tempo",
            stat_modifiers={
                "spd": tempo * 3,
                "effect_hit_rate": tempo * 0.05,
            },
            duration=2,
            source=self.id,
        )
        target.add_effect(tempo_effect)

    async def on_hit_landed(
        self,
        attacker: "Stats",
        target_hit: "Stats",
        damage: int,
        action_type: str,
        **kwargs,
    ) -> None:
        """Apply shock slow and attack overload after landing a hit."""

        await self.on_hit_target(attacker, target_hit, damage=damage)

    async def on_hit_target(
        self,
        attacker: "Stats",
        target_hit: "Stats",
        damage: int | None = None,
    ) -> None:
        if target_hit is None:
            return

        attacker_id = id(attacker)
        tempo = self._tempo_stacks.get(attacker_id, 0)
        if tempo <= 0:
            return

        key = (attacker_id, id(target_hit))
        shock = min(self._shock_stacks.get(key, 0) + 1, 5)
        self._shock_stacks[key] = shock

        slow_amount = -2 * max(1, tempo)
        resistance_penalty = -0.03 * shock

        shock_effect = StatEffect(
            name=f"{self.id}_shock_{attacker_id}",
            stat_modifiers={
                "spd": slow_amount,
                "effect_resistance": resistance_penalty,
            },
            duration=2,
            source=self.id,
        )
        target_hit.add_effect(shock_effect)

        attack_bonus = int(attacker.atk * 0.04 * min(tempo, 3))
        if attack_bonus > 0:
            overload_effect = StatEffect(
                name=f"{self.id}_overload",
                stat_modifiers={"atk": attack_bonus},
                duration=1,
                source=self.id,
            )
            attacker.add_effect(overload_effect)

        # Consuming the stored tempo charge ensures new actions are required to
        # rebuild Stormsurge stacks, matching the passive description.
        self._tempo_stacks[attacker_id] = 0

    async def on_defeat(self, target: "Stats") -> None:
        """Clear tempo and shock tracking when Lady Lightning is defeated."""

        entity_id = id(target)
        self._tempo_stacks.pop(entity_id, None)
        to_delete = [key for key in self._shock_stacks if key[0] == entity_id]
        for key in to_delete:
            del self._shock_stacks[key]

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Expose current tempo stacks for UI display."""

        return cls._tempo_stacks.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Acts charge up to four Stormsurge stacks, granting +3 Speed and +5% effect "
            "hit per stack. Landing hits consumes the stored charge to inflict a "
            "two-turn shock that slows foes and strips 3% effect resistance per stack "
            "while briefly overloading Lady Lightning's attack."
        )
