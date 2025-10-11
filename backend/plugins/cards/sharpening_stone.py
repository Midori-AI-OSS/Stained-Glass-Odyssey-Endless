from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class SharpeningStone(CardBase):
    id: str = "sharpening_stone"
    name: str = "Sharpening Stone"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"crit_damage": 0.03})
    about: str = "+3% Crit Damage; After scoring a crit, gain +2% crit damage for 2 turns"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_critical_hit(attacker, target, damage, action_name):
            # Check if attacker is one of our party members
            if attacker in party.members:
                # Grant +2% crit damage for 2 turns
                effect_manager = getattr(attacker, 'effect_manager', None)
                if effect_manager is None:
                    effect_manager = EffectManager(attacker)
                    attacker.effect_manager = effect_manager

                # Create temporary crit damage buff
                crit_damage_mod = create_stat_buff(
                    attacker,
                    name=f"{self.id}_crit_boost",
                    turns=2,
                    crit_damage_mult=1.02  # +2% crit damage
                )
                await effect_manager.add_modifier(crit_damage_mod)

                import logging
                log = logging.getLogger(__name__)
                log.debug("Sharpening Stone crit damage boost: +2% crit damage for 2 turns to %s", attacker.id)
                await BUS.emit_async("card_effect", self.id, attacker, "crit_damage_boost", 2, {
                    "crit_damage_boost": 2,
                    "duration": 2,
                    "trigger_event": "critical_hit"
                })

        self.subscribe("critical_hit", _on_critical_hit)
