from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class BalancedDiet(CardBase):
    id: str = "balanced_diet"
    name: str = "Balanced Diet"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"max_hp": 0.03, "defense": 0.03})
    about: str = "+3% HP & +3% DEF; When healed, grant the healed unit +2% DEF for 1 turn"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_heal_received(target, healer, heal_amount, *_args):
            # Check if target is one of our party members
            if target in party.members:
                # Grant +2% DEF for 1 turn
                effect_manager = getattr(target, 'effect_manager', None)
                if effect_manager is None:
                    effect_manager = EffectManager(target)
                    target.effect_manager = effect_manager

                # Create temporary DEF buff
                def_mod = create_stat_buff(
                    target,
                    name=f"{self.id}_heal_def",
                    turns=1,
                    defense_mult=1.02  # +2% DEF
                )
                effect_manager.add_modifier(def_mod)

                import logging
                log = logging.getLogger(__name__)
                log.debug("Balanced Diet heal bonus: +2% DEF for 1 turn to %s", target.id)
                await BUS.emit_async("card_effect", self.id, target, "heal_def_bonus", 2, {
                    "def_bonus": 2,
                    "duration": 1,
                    "trigger_event": "heal_received",
                    "heal_amount": heal_amount
                })

        self.subscribe("heal_received", _on_heal_received)
