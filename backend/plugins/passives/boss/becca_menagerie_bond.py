from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.becca_menagerie_bond import BeccaMenagerieBond

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class BeccaMenagerieBondBoss(BeccaMenagerieBond):
    """Boss-tier Menagerie Bond that leans harder on spirit carryover bonuses."""

    plugin_type = "passive"
    id = "becca_menagerie_bond_boss"
    name = "Menagerie Bond (Boss)"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats") -> None:
        """Refresh spirit bonuses at 1.5× strength and keep jellyfish synchronized."""

        from autofighter.stat_effect import StatEffect
        from autofighter.summons.manager import SummonManager

        entity_key = self._resolve_entity_key(target)
        summoner_id = self._get_summoner_id(target)

        if hasattr(target, "ensure_permanent_summon_slots"):
            target.ensure_permanent_summon_slots(1)

        setattr(target, "_becca_menagerie_passive", self)

        if entity_key not in self._summon_cooldown:
            self._summon_cooldown[entity_key] = 0
            self._spirit_stacks[entity_key] = 0
            self._applied_spirit_stacks[entity_key] = 0
            self._buffed_summons[entity_key] = set()

        current_spirit_stacks = self._spirit_stacks[entity_key]
        applied_stacks = self._applied_spirit_stacks.get(entity_key, 0)

        summons = SummonManager.get_summons(summoner_id)
        jellyfish_summons = [s for s in summons if s.summon_source == self.id]
        current_ids = {id(s) for s in jellyfish_summons}
        buffed_ids = self._buffed_summons.setdefault(entity_key, set())

        spirit_effect_name = f"{self.id}_spirit_bonuses"
        pet_effect_name = f"{self.id}_pet_spirit_bonuses"

        def _has_effect(entity: "Stats", effect_name: str) -> bool:
            if not hasattr(entity, "get_active_effects"):
                return False
            try:
                active_effects = entity.get_active_effects()
            except Exception:
                return False
            return any(effect.name == effect_name for effect in active_effects)

        refresh_required = current_spirit_stacks != applied_stacks
        if current_spirit_stacks > 0 and not _has_effect(target, spirit_effect_name):
            refresh_required = True

        if current_spirit_stacks > 0:
            missing_summon_effects = {
                id(summon)
                for summon in jellyfish_summons
                if not _has_effect(summon, pet_effect_name)
            }
            if missing_summon_effects:
                buffed_ids.difference_update(missing_summon_effects)

        def _spirit_bonus() -> tuple[int, int]:
            atk = int(target._base_atk * 0.075 * current_spirit_stacks)
            defense = int(target._base_defense * 0.075 * current_spirit_stacks)
            return atk, defense

        if refresh_required:
            spirit_attack_bonus, spirit_defense_bonus = _spirit_bonus()
            spirit_effect = StatEffect(
                name=spirit_effect_name,
                stat_modifiers={
                    "atk": spirit_attack_bonus,
                    "defense": spirit_defense_bonus,
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(spirit_effect)

            for summon in jellyfish_summons:
                pet_effect = StatEffect(
                    name=pet_effect_name,
                    stat_modifiers={
                        "atk": spirit_attack_bonus,
                        "defense": spirit_defense_bonus,
                    },
                    duration=-1,
                    source=self.id,
                )
                summon.add_effect(pet_effect)

            self._applied_spirit_stacks[entity_key] = current_spirit_stacks
            self._buffed_summons[entity_key] = current_ids
        else:
            new_ids = current_ids - buffed_ids
            if new_ids:
                spirit_attack_bonus, spirit_defense_bonus = _spirit_bonus()
                for summon in jellyfish_summons:
                    if id(summon) in new_ids:
                        pet_effect = StatEffect(
                            name=pet_effect_name,
                            stat_modifiers={
                                "atk": spirit_attack_bonus,
                                "defense": spirit_defense_bonus,
                            },
                            duration=-1,
                            source=self.id,
                        )
                        summon.add_effect(pet_effect)
                buffed_ids.update(new_ids)
            buffed_ids.intersection_update(current_ids)

        if self._summon_cooldown[entity_key] > 0:
            self._summon_cooldown[entity_key] -= 1

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Spend 10% current HP to summon a jellyfish. "
            "Retired jellyfish leave spirits that grant +7.5% attack and defense per stack to Becca and her pets, "
            "letting boss fights snowball without touching normal passives."
        )
