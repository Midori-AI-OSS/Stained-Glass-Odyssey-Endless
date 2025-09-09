from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Optional

from autofighter.stats import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class CarlyGuardiansAegis:
    """Carly's Guardian's Aegis passive - tank mechanics with healing and mitigation."""

    plugin_type = "passive"
    id = "carly_guardians_aegis"
    name = "Guardian's Aegis"
    trigger = "turn_start"  # Triggers at start of turn for healing
    max_stacks = 50  # Soft cap - show mitigation stacks with diminished returns past 50
    stack_display = "number"

    # Class-level tracking of mitigation stacks and converted defense stacks
    _mitigation_stacks: ClassVar[dict[int, int]] = {}
    _attack_baseline: ClassVar[dict[int, int]] = {}
    _defense_stacks: ClassVar[dict[int, int]] = {}
    _overcharged: ClassVar[dict[int, bool]] = {}

    async def apply(
        self, target: "Stats", party: Optional[list["Stats"]] = None, **_: object
    ) -> None:
        """Apply Carly's Guardian's Aegis healing and conversion mechanics."""
        entity_id = id(target)

        # Initialize tracking dictionaries
        if entity_id not in self._mitigation_stacks:
            self._mitigation_stacks[entity_id] = 0
        if entity_id not in self._attack_baseline:
            # Record Carly's starting base attack to measure future growth
            self._attack_baseline[entity_id] = int(target.get_base_stat("atk"))
        if entity_id not in self._defense_stacks:
            self._defense_stacks[entity_id] = 0
        if entity_id not in self._overcharged:
            self._overcharged[entity_id] = False

        if self._overcharged[entity_id]:
            self._mitigation_stacks[entity_id] = max(
                0, self._mitigation_stacks[entity_id] - 5
            )
            if self._mitigation_stacks[entity_id] <= 10:
                self._overcharged[entity_id] = False
                target.remove_effect_by_name(f"{self.id}_overcharged_atk")
            else:
                target.remove_effect_by_name(f"{self.id}_overcharged_atk")
                overcharge_effect = StatEffect(
                    name=f"{self.id}_overcharged_atk",
                    stat_modifiers={"atk": target.defense},
                    duration=-1,
                    source=self.id,
                )
                target.add_effect(overcharge_effect)

        # Convert any attack growth into permanent defense stacks
        base_atk = self._attack_baseline[entity_id]
        current_atk = int(target.get_base_stat("atk"))
        growth = current_atk - base_atk
        if growth > 0:
            self._defense_stacks[entity_id] += growth
            target.set_base_stat("atk", base_atk)

            stacks = self._defense_stacks[entity_id]
            base_defense = min(stacks, 50)
            excess_stacks = max(0, stacks - 50)
            defense_bonus = base_defense + excess_stacks * 0.5

            defense_effect = StatEffect(
                name=f"{self.id}_defense_stacks",
                stat_modifiers={"defense": defense_bonus},
                duration=-1,
                source=self.id,
            )
            target.add_effect(defense_effect)

        # Heal the most injured ally or self if none injured
        defense_based_heal = int(target.defense * 0.1)
        injured: Optional["Stats"] = None
        if party:
            injured = min(
                (a for a in party if a.hp < a.max_hp),
                key=lambda a: a.hp / a.max_hp,
                default=None,
            )
        recipient = injured if injured is not None else target

        await recipient.apply_healing(defense_based_heal, healer=target)

        heal_effect = StatEffect(
            name=f"{self.id}_defense_heal",
            stat_modifiers={"hp": defense_based_heal},
            duration=1,
            source=self.id,
        )
        recipient.add_effect(heal_effect)

        # Apply accumulated mitigation stacks from previous hits with soft cap logic
        if self._mitigation_stacks[entity_id] > 0:
            current_stacks = self._mitigation_stacks[entity_id]
            base_mitigation = min(current_stacks, 50) * 0.02
            excess_stacks = max(0, current_stacks - 50)
            excess_mitigation = excess_stacks * 0.01
            total_mitigation = base_mitigation + excess_mitigation

            mitigation_effect = StatEffect(
                name=f"{self.id}_mitigation_stacks",
                stat_modifiers={"mitigation": total_mitigation},
                duration=-1,
                source=self.id,
            )
            target.add_effect(mitigation_effect)

    async def on_damage_taken(
        self, target: "Stats", attacker: "Stats", damage: int
    ) -> None:
        """Handle Carly's damage mitigation mechanics when hit."""
        entity_id = id(target)

        # Initialize mitigation stack tracking if not present
        if entity_id not in self._mitigation_stacks:
            self._mitigation_stacks[entity_id] = 0
        if entity_id not in self._overcharged:
            self._overcharged[entity_id] = False

        # Apply mitigation twice (square mitigation)
        # This would need integration with damage calculation system
        # For now, apply a temporary defensive bonus
        squared_mitigation_bonus = target.mitigation * 0.1  # 10% bonus mitigation

        double_mitigation_effect = StatEffect(
            name=f"{self.id}_squared_mitigation",
            stat_modifiers={"mitigation": squared_mitigation_bonus},
            duration=1,  # For this hit only
            source=self.id,
        )
        target.add_effect(double_mitigation_effect)

        # Gain two mitigation stacks for rest of fight (unless overcharged)
        if not self._overcharged[entity_id]:
            self._mitigation_stacks[entity_id] += 2
            if self._mitigation_stacks[entity_id] > 100:
                self._overcharged[entity_id] = True
                overcharge_effect = StatEffect(
                    name=f"{self.id}_overcharged_atk",
                    stat_modifiers={"atk": target.defense},
                    duration=-1,
                    source=self.id,
                )
                target.add_effect(overcharge_effect)

        # Apply taunt effect (force enemies to target Carly)
        # This would need battle system integration
        taunt_effect = StatEffect(
            name=f"{self.id}_taunt",
            stat_modifiers={"taunt_level": 1.0},  # High priority target
            duration=2,  # Two turns of taunt
            source=self.id,
        )
        target.add_effect(taunt_effect)

    async def on_ultimate_use(self, target: "Stats", party: list["Stats"]) -> None:
        """Handle ultimate ability effects - distribute mitigation to allies."""
        allies = [member for member in party if member is not target]
        if not allies:
            return

        total_share = target.mitigation * 0.5
        per_ally = total_share / len(allies)
        for ally in allies:
            ally_mitigation_effect = StatEffect(
                name=f"{self.id}_shared_mitigation",
                stat_modifiers={"mitigation": per_ally},
                duration=3,
                source=self.id,
            )
            ally.add_effect(ally_mitigation_effect)

        mitigation_reduction_effect = StatEffect(
            name=f"{self.id}_mitigation_reduction",
            stat_modifiers={"mitigation": -total_share},
            duration=3,
            source=self.id,
        )
        target.add_effect(mitigation_reduction_effect)

    @classmethod
    def get_mitigation_stacks(cls, target: "Stats") -> int:
        """Get current mitigation stacks for an entity."""
        return cls._mitigation_stacks.get(id(target), 0)

    @classmethod
    def get_stacks(cls, target: "Stats") -> dict[str, int | bool]:
        """Return current mitigation stacks and overcharge status for UI display."""
        entity_id = id(target)
        return {
            "mitigation": cls._mitigation_stacks.get(entity_id, 0),
            "overcharged": cls._overcharged.get(entity_id, False),
        }

    @classmethod
    def get_description(cls) -> str:
        return (
            "Heals the most injured ally for 10% of Carly's defense each turn. "
            "Attack gains convert into defense stacks up to 50. "
            "Taking hits builds mitigation stacks that can overcharge and share defense."
        )
