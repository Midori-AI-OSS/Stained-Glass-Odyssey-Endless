from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.becca_menagerie_bond import BeccaMenagerieBond

if TYPE_CHECKING:
    from autofighter.party import Party
    from autofighter.stats import Stats


@dataclass
class BeccaMenagerieBondPrime(BeccaMenagerieBond):
    """[PRIME] Becca summons hardier jellyfish and fattens spirit bonds."""

    plugin_type = "passive"
    id = "becca_menagerie_bond_prime"
    name = "Prime Menagerie Bond"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats") -> None:
        entity_key = self._resolve_entity_key(target)
        self._summon_cooldown.setdefault(entity_key, 0)
        self._spirit_stacks.setdefault(entity_key, 0)
        self._applied_spirit_stacks.setdefault(entity_key, 0)
        self._buffed_summons.setdefault(entity_key, set())

        await super().apply(target)

        current_spirit_stacks = self._spirit_stacks[entity_key]
        spirit_attack_bonus = int(target._base_atk * 0.08 * current_spirit_stacks)
        spirit_defense_bonus = int(target._base_defense * 0.08 * current_spirit_stacks)

        if current_spirit_stacks > 0:
            spirit_effect = StatEffect(
                name=f"{self.id}_spirit_bonuses",
                stat_modifiers={
                    "atk": spirit_attack_bonus,
                    "defense": spirit_defense_bonus,
                    "regain": max(1, int(target.max_hp * 0.005 * current_spirit_stacks)),
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(spirit_effect)

    async def summon_jellyfish(
        self,
        target: "Stats",
        jellyfish_type: str | None = None,
        party: "Party | None" = None,
    ) -> bool:
        """Prime version summons sturdier allies for a lighter HP cost."""

        entity_key = self._resolve_entity_key(target)
        self._summon_cooldown.setdefault(entity_key, 0)
        self._spirit_stacks.setdefault(entity_key, 0)

        if self._summon_cooldown[entity_key] > 0:
            return False

        hp_cost = int(target.hp * 0.05)
        if target.hp <= hp_cost:
            return False

        target.hp -= hp_cost
        success = await super().summon_jellyfish(
            target,
            jellyfish_type=jellyfish_type,
            party=party,
        )

        if success:
            self._summon_cooldown[entity_key] = 0
        return success

    async def _create_spirit(self, target: "Stats") -> None:
        self._spirit_stacks[self._resolve_entity_key(target)] = (
            self._spirit_stacks.get(self._resolve_entity_key(target), 0) + 2
        )
        await super()._create_spirit(target)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Summons cost only 5% current HP and return at full strength. "
            "Each lost jellyfish grants two spirit stacks, giving +8% ATK/DEF and minor regen per stack to Becca and her pets."
        )

