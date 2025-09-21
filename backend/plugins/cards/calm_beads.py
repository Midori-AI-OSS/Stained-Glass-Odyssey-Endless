from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class CalmBeads(CardBase):
    id: str = "calm_beads"
    name: str = "Calm Beads"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"effect_resistance": 0.03})
    about: str = "+3% Effect Res; On resisting a debuff, gain +1 small ultimate charge for next action"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_effect_resisted(effect_name, target, source, details=None):
            if target not in party.members:
                return

            metadata = details or {}
            effect_lower = (effect_name or "").lower()
            effect_type = metadata.get("effect_type")
            is_debuff = effect_type in {"dot", "debuff"}
            if not is_debuff:
                is_debuff = any(
                    keyword in effect_lower
                    for keyword in [
                        'bleed',
                        'poison',
                        'burn',
                        'freeze',
                        'stun',
                        'silence',
                        'slow',
                        'weakness',
                        'curse',
                        'dot',
                        'debuff',
                    ]
                )

            if not is_debuff:
                return

            target.add_ultimate_charge(1)
            import logging
            log = logging.getLogger(__name__)
            log.debug("Calm Beads ultimate charge refund: +1 charge to %s", target.id)
            payload = {
                "charge_gained": 1,
                "resisted_effect": effect_name,
                "trigger_event": "effect_resisted",
            }
            if metadata:
                payload["metadata"] = metadata
            await BUS.emit_async("card_effect", self.id, target, "resist_charge_gain", 1, payload)

        self.subscribe("effect_resisted", _on_effect_resisted)
