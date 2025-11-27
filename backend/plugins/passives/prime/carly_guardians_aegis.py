from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Optional

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.carly_guardians_aegis import CarlyGuardiansAegis

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class CarlyGuardiansAegisPrime(CarlyGuardiansAegis):
    """[PRIME] Guardian's Aegis with higher conversions and sustain."""

    plugin_type = "passive"
    id = "carly_guardians_aegis_prime"
    name = "Prime Guardian's Aegis"
    trigger = "turn_start"
    max_stacks = 70
    stack_display = "number"

    async def apply(self, target: "Stats", party: Optional[list["Stats"]] = None, **_: object) -> None:
        entity_id = id(target)
        self._mitigation_stacks.setdefault(entity_id, 0)
        self._attack_baseline.setdefault(entity_id, int(target.get_base_stat("atk")))
        self._defense_stacks.setdefault(entity_id, 0)
        self._overcharged.setdefault(entity_id, False)

        await super().apply(target, party=party)

        defense_based_heal = int(target.defense * 0.15)
        recipient = min(party or [target], key=lambda a: (a.hp / a.max_hp) if getattr(a, "max_hp", 0) else 1)
        await recipient.apply_healing(defense_based_heal, healer=target)

    async def on_damage_taken(self, target: "Stats", attacker: "Stats", damage: int) -> None:
        entity_id = id(target)
        self._mitigation_stacks.setdefault(entity_id, 0)
        self._overcharged.setdefault(entity_id, False)

        squared_mitigation_bonus = target.mitigation * 0.2
        mitigation_effect = StatEffect(
            name=f"{self.id}_squared_mitigation",
            stat_modifiers={"mitigation": squared_mitigation_bonus},
            duration=1,
            source=self.id,
        )
        target.add_effect(mitigation_effect)

        if not self._overcharged[entity_id]:
            self._mitigation_stacks[entity_id] += 3
            if self._mitigation_stacks[entity_id] > 80:
                self._overcharged[entity_id] = True
                overcharge_effect = StatEffect(
                    name=f"{self.id}_overcharged_atk",
                    stat_modifiers={"atk": int(target.defense * 1.25)},
                    duration=-1,
                    source=self.id,
                )
                target.add_effect(overcharge_effect)

        taunt_effect = StatEffect(
            name=f"{self.id}_taunt",
            stat_modifiers={"taunt_level": 1.0},
            duration=3,
            source=self.id,
        )
        target.add_effect(taunt_effect)

    async def on_ultimate_use(self, target: "Stats", party: list["Stats"]) -> None:
        allies = [member for member in party if member is not target]
        if not allies:
            return

        total_share = target.mitigation * 0.75
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
            stat_modifiers={"mitigation": -total_share * 0.5},
            duration=3,
            source=self.id,
        )
        target.add_effect(mitigation_reduction_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Heals allies for 15% of Carly's defense each turn and converts attack growth into heavier defense. "
            "Takes 3 mitigation stacks per hit, overcharging at 80 stacks to add 125% defense as attack. "
            "Ultimate shares 75% of Carly's mitigation with allies while halving the self-penalty."
        )

