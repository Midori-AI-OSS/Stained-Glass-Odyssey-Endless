from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.becca_menagerie_bond import BeccaMenagerieBond

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class BeccaMenagerieBondGlitched(BeccaMenagerieBond):
    """[GLITCHED] Becca's Menagerie Bond - jellyfish with doubled spirit bonuses.

    This glitched variant doubles the stat bonuses from spirits (+10% attack and defense
    per stack instead of +5%), making the spirit accumulation significantly more powerful
    while maintaining the same jellyfish summoning mechanics and HP cost.
    """
    plugin_type = "passive"
    id = "becca_menagerie_bond_glitched"
    name = "Glitched Menagerie Bond"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats") -> None:
        """Apply Menagerie Bond with DOUBLED spirit bonuses."""
        from autofighter.stat_effect import StatEffect
        from autofighter.summons.manager import SummonManager

        entity_key = self._resolve_entity_key(target)
        summoner_id = self._get_summoner_id(target)

        if hasattr(target, "ensure_permanent_summon_slots"):
            target.ensure_permanent_summon_slots(1)

        setattr(target, "_becca_menagerie_passive", self)

        # Initialize tracking if not present
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

        if refresh_required:
            # DOUBLED spirit bonuses (10% instead of 5%)
            spirit_attack_bonus = int(target._base_atk * 0.10 * current_spirit_stacks)  # Doubled
            spirit_defense_bonus = int(target._base_defense * 0.10 * current_spirit_stacks)  # Doubled

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
                # DOUBLED spirit bonuses (10% instead of 5%)
                spirit_attack_bonus = int(target._base_atk * 0.10 * current_spirit_stacks)  # Doubled
                spirit_defense_bonus = int(target._base_defense * 0.10 * current_spirit_stacks)  # Doubled
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

        # Handle summon cooldown
        if self._summon_cooldown[entity_key] > 0:
            self._summon_cooldown[entity_key] -= 1

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Spend 10% current HP to summon a jellyfish. "
            "Each former jellyfish leaves a spirit granting +10% attack and defense (doubled) per stack."
        )
