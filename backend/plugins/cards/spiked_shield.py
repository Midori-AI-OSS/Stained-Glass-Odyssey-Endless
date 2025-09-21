from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task

log = logging.getLogger(__name__)


@dataclass
class SpikedShield(CardBase):
    id: str = "spiked_shield"
    name: str = "Spiked Shield"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.03, "defense": 0.03})
    about: str = "+3% ATK & +3% DEF; When mitigation triggers (block threshold), deal small retaliatory damage (3% of attack)"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        def _on_mitigation_triggered(target, original_damage, mitigated_damage, attacker=None):
            if (
                attacker is not None
                and target in party.members
                and mitigated_damage < original_damage
            ):
                atk_stat = getattr(target, "atk", 0)
                if atk_stat == 0:
                    atk_stat = getattr(target, "attack", 0)
                retaliation_damage = int(atk_stat * 0.03)

                if retaliation_damage > 0:
                    async def _retaliate():
                        try:
                            dealt = await attacker.apply_damage(
                                retaliation_damage,
                                attacker=target,
                                action_name="Spiked Shield Retaliation",
                            )
                        except Exception as e:  # pragma: no cover - defensive
                            log.warning(
                                "Error applying Spiked Shield retaliation damage: %s",
                                e,
                            )
                            return
                        log.debug(
                            "Spiked Shield retaliation: %d damage from %s to %s",
                            dealt,
                            target.id,
                            getattr(attacker, "id", "unknown"),
                        )
                        await BUS.emit_async(
                            "card_effect",
                            self.id,
                            target,
                            "retaliation_damage",
                            dealt,
                            {
                                "retaliation_damage": dealt,
                                "damage_mitigated": original_damage - mitigated_damage,
                                "trigger_event": "mitigation",
                                "retaliation_target": getattr(attacker, "id", "unknown"),
                            },
                        )

                    safe_async_task(_retaliate())

        self.subscribe("mitigation_triggered", _on_mitigation_triggered)
