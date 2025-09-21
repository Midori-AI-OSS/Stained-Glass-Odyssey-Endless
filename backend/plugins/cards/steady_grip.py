from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class SteadyGrip(CardBase):
    id: str = "steady_grip"
    name: str = "Steady Grip"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.03, "dodge_odds": 0.03})
    about: str = "+3% ATK & +3% Dodge Odds; On applying a control effect (stun/silence), gain +2% ATK for next action"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_effect_applied(target, effect_name, duration, source):
            # Check if source is one of our party members and effect is a control effect
            if source in party.members:
                effect_lower = effect_name.lower()
                is_control = any(keyword in effect_lower for keyword in ['stun', 'silence', 'freeze', 'paralyze'])

                if is_control:
                    # Grant +2% ATK for next action
                    effect_manager = getattr(source, 'effect_manager', None)
                    if effect_manager is None:
                        effect_manager = EffectManager(source)
                        source.effect_manager = effect_manager

                    # Create temporary ATK buff
                    atk_mod = create_stat_buff(
                        source,
                        name=f"{self.id}_control_atk",
                        turns=1,
                        atk_mult=1.02  # +2% ATK
                    )
                    effect_manager.add_modifier(atk_mod)

                    import logging
                    log = logging.getLogger(__name__)
                    log.debug("Steady Grip control bonus: +2%% ATK for next action to %s", source.id)
                    await BUS.emit_async("card_effect", self.id, source, "control_atk_bonus", 2, {
                        "atk_bonus": 2,
                        "duration": 1,
                        "control_effect": effect_name,
                        "trigger_event": "control_applied"
                    })

        self.subscribe("effect_applied", _on_effect_applied)
