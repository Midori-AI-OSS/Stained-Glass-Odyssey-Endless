from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class LightweightBoots(CardBase):
    id: str = "lightweight_boots"
    name: str = "Lightweight Boots"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"dodge_odds": 0.03})
    about: str = "+3% Dodge Odds; On successful dodge, heal 2% HP to the dodging unit"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_dodge(dodger, attacker, original_damage, *_extra):
            # Check if dodger is one of our party members
            if dodger in party.members:
                # Heal 2% HP
                max_hp = getattr(dodger, "max_hp", 1)
                heal_amount = int(max_hp * 0.02)
                if heal_amount > 0:
                    import logging
                    log = logging.getLogger(__name__)
                    try:
                        await dodger.apply_healing(
                            heal_amount,
                            source_type="dodge_heal",
                            source_name="lightweight_boots",
                        )
                        log.debug(
                            "Lightweight Boots dodge heal: +%d HP to %s",
                            heal_amount,
                            dodger.id,
                        )
                        await BUS.emit_async(
                            "card_effect",
                            self.id,
                            dodger,
                            "dodge_heal",
                            heal_amount,
                            {
                                "heal_amount": heal_amount,
                                "trigger_event": "dodge",
                            },
                        )
                    except Exception as e:
                        log.warning("Error applying Lightweight Boots dodge heal: %s", e)

        def _on_battle_end(_entity) -> None:
            BUS.unsubscribe("dodge", _on_dodge)
            BUS.unsubscribe("battle_end", _on_battle_end)

        BUS.subscribe("dodge", _on_dodge)
        BUS.subscribe("battle_end", _on_battle_end)
