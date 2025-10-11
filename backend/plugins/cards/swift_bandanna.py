from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class SwiftBandanna(CardBase):
    id: str = "swift_bandanna"
    name: str = "Swift Bandanna"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"crit_rate": 0.03, "dodge_odds": 0.03})
    about: str = "+3% Crit Rate & +3% Dodge Odds; On dodge, gain +1% crit rate for next action"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_dodge(dodger, attacker, original_damage):
            # Check if dodger is one of our party members
            if dodger in party.members:
                # Grant +1% crit rate for next action
                effect_manager = getattr(dodger, 'effect_manager', None)
                if effect_manager is None:
                    effect_manager = EffectManager(dodger)
                    dodger.effect_manager = effect_manager

                # Create temporary crit rate buff
                crit_mod = create_stat_buff(
                    dodger,
                    name=f"{self.id}_dodge_crit",
                    turns=1,
                    crit_rate_mult=1.01  # +1% crit rate
                )
                await effect_manager.add_modifier(crit_mod)

                import logging
                log = logging.getLogger(__name__)
                log.debug("Swift Bandanna dodge bonus: +1%% crit rate for next action to %s", dodger.id)
                await BUS.emit_async("card_effect", self.id, dodger, "dodge_crit_bonus", 1, {
                    "crit_rate_bonus": 1,
                    "duration": 1,
                    "trigger_event": "dodge"
                })

        self.subscribe("dodge", _on_dodge)
