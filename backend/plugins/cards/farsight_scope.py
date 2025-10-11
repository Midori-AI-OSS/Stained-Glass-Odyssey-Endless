from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class FarsightScope(CardBase):
    id: str = "farsight_scope"
    name: str = "Farsight Scope"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"crit_rate": 0.03})
    about: str = "+3% Crit Rate; Attacks against enemies under 50% HP gain +6% crit rate"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _before_attack(attacker, target, *_extra):
            if attacker in party.members:
                target_hp = getattr(target, "hp", 0)
                target_max_hp = getattr(target, "max_hp", 1)
                if target_hp / target_max_hp < 0.50:
                    log = logging.getLogger(__name__)

                    effect_manager = getattr(attacker, "effect_manager", None)
                    if effect_manager is None:
                        effect_manager = EffectManager(attacker)
                        attacker.effect_manager = effect_manager

                    crit_mod = create_stat_buff(
                        attacker,
                        name=f"{self.id}_low_hp_crit",
                        turns=1,
                        crit_rate=0.06,
                    )
                    await effect_manager.add_modifier(crit_mod)

                    log.debug(
                        "Farsight Scope low HP bonus: %s gains +6%% crit rate vs %s",
                        getattr(attacker, "id", "attacker"),
                        getattr(target, "id", "target"),
                    )
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        attacker,
                        "low_hp_crit_bonus",
                        6,
                        {
                            "crit_rate_bonus": 6,
                            "target_hp_percentage": (target_hp / target_max_hp) * 100,
                            "trigger_threshold": 50,
                        },
                    )

                    def _remove_bonus(actor, *_args):
                        if actor is attacker:
                            crit_mod.remove()
                            log.debug(
                                "Farsight Scope crit bonus removed from %s",
                                getattr(attacker, "id", "attacker"),
                            )
                            self.unsubscribe("action_used", _remove_bonus)

                    self.subscribe("action_used", _remove_bonus)

        self.subscribe("before_attack", _before_attack)
