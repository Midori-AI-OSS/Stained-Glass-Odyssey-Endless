from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class CoatedArmor(CardBase):
    id: str = "coated_armor"
    name: str = "Coated Armor"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"mitigation": 0.03, "defense": 0.03})
    about: str = "+3% Mitigation & +3% DEF; When mitigation reduces incoming damage, heal 1% HP"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_mitigation_triggered(target, original_damage, mitigated_damage):
            # Check if target is one of our party members and mitigation actually reduced damage
            if target in party.members and mitigated_damage < original_damage:
                # Heal 1% HP
                max_hp = getattr(target, "max_hp", 1)
                heal_amount = int(max_hp * 0.01)
                if heal_amount > 0:
                    import asyncio
                    import logging

                    log = logging.getLogger(__name__)
                    try:
                        asyncio.create_task(
                            target.apply_healing(
                                heal_amount,
                                source_type="mitigation_heal",
                                source_name="coated_armor",
                            )
                        )
                        log.debug(
                            "Coated Armor mitigation heal: +%d HP to %s",
                            heal_amount,
                            target.id,
                        )
                        await BUS.emit_async(
                            "card_effect",
                            self.id,
                            target,
                            "mitigation_heal",
                            heal_amount,
                            {
                                "heal_amount": heal_amount,
                                "damage_mitigated": original_damage - mitigated_damage,
                                "trigger_event": "mitigation",
                            },
                        )
                    except Exception as e:  # pragma: no cover - defensive
                        log.warning(
                            "Error applying Coated Armor mitigation heal: %s",
                            e,
                        )

        def _on_battle_end(_entity) -> None:
            self.cleanup_subscriptions()

        self.subscribe("mitigation_triggered", _on_mitigation_triggered)
        self.subscribe("battle_end", _on_battle_end)
