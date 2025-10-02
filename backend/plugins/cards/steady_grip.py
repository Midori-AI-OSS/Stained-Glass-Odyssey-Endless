from dataclasses import dataclass
from dataclasses import field
import logging
import random

from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task

log = logging.getLogger(__name__)


@dataclass
class SteadyGrip(CardBase):
    id: str = "steady_grip"
    name: str = "Steady Grip"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.05})
    about: str = (
        "+5% ATK; Critical hits can become super crits, dealing 4× total damage"
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_critical_hit(attacker, target, damage, action_name):
            if attacker not in party.members:
                return

            crit_rate = float(getattr(attacker, "crit_rate", 0.0) or 0.0)
            super_crit_chance = min(max(crit_rate * 0.2, 0.0), 1.0)
            roll = random.random()
            log.debug(
                "Steady Grip super crit roll: %s chance=%s for attacker=%s",
                roll,
                super_crit_chance,
                getattr(attacker, "id", "unknown"),
            )
            if roll >= super_crit_chance:
                return

            bonus_damage = int(damage * 3)
            if bonus_damage <= 0:
                return

            log.debug(
                "Steady Grip applying bonus damage: %s to target=%s",
                bonus_damage,
                getattr(target, "id", "unknown"),
            )
            safe_async_task(
                target.apply_damage(
                    bonus_damage,
                    attacker,
                    trigger_on_hit=False,
                    action_name="steady_grip_super_crit",
                )
            )
            await BUS.emit_async(
                "card_effect",
                self.id,
                attacker,
                "super_crit",
                bonus_damage,
                {
                    "trigger_event": "critical_hit",
                    "bonus_damage": bonus_damage,
                    "chance": super_crit_chance,
                    "roll": roll,
                    "action_name": action_name,
                },
            )

        self.subscribe("critical_hit", _on_critical_hit)
