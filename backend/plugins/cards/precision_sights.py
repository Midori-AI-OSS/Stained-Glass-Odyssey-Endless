from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class PrecisionSights(CardBase):
    id: str = "precision_sights"
    name: str = "Precision Sights"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"crit_damage": 0.04})
    about: str = "+4% Crit Damage; After scoring a crit, gain +2% crit damage for 2 turns (small stacking)"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_critical_hit(attacker, target, damage, action_name):
            # Check if attacker is one of our party members
            if attacker in party.members:
                # Grant +2% crit damage for 2 turns (stacking)
                effect_manager = getattr(attacker, 'effect_manager', None)
                if effect_manager is None:
                    effect_manager = EffectManager(attacker)
                    attacker.effect_manager = effect_manager

                # Create temporary crit damage buff (allows stacking)
                import time
                unique_suffix = int(time.time() * 1000) % 10000  # Unique identifier for stacking
                crit_damage_mod = create_stat_buff(
                    attacker,
                    name=f"{self.id}_crit_boost_{unique_suffix}",
                    turns=2,
                    crit_damage_mult=1.02,  # +2% crit damage
                )
                await effect_manager.add_modifier(crit_damage_mod)

                import logging
                log = logging.getLogger(__name__)
                log.debug("Precision Sights crit damage boost: +2% crit damage for 2 turns to %s (stacking)", attacker.id)
                await BUS.emit_async("card_effect", self.id, attacker, "crit_damage_boost", 2, {
                    "crit_damage_boost": 2,
                    "duration": 2,
                    "stacking": True,
                    "trigger_event": "critical_hit"
                })

        self.subscribe("critical_hit", _on_critical_hit)
