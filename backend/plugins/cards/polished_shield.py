from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class PolishedShield(CardBase):
    id: str = "polished_shield"
    name: str = "Polished Shield"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.03})
    about: str = "+3% DEF; When an ally resists a DoT/debuff, grant them +3 DEF for 1 turn"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        def _on_effect_resisted(effect_name, target, source, details=None):
            if target not in party.members:
                return

            metadata = details or {}
            effect_lower = (effect_name or "").lower()
            effect_type = metadata.get("effect_type")
            is_dot_or_debuff = effect_type in {"dot", "debuff"}
            if not is_dot_or_debuff:
                is_dot_or_debuff = any(
                    keyword in effect_lower
                    for keyword in ['bleed', 'poison', 'burn', 'freeze', 'stun', 'silence', 'slow', 'weakness', 'curse']
                )

            if not is_dot_or_debuff:
                return

            effect_manager = getattr(target, 'effect_manager', None)
            if effect_manager is None:
                effect_manager = EffectManager(target)
                target.effect_manager = effect_manager

            def_mod = create_stat_buff(
                target,
                name=f"{self.id}_resist_def",
                turns=1,
                defense=3
            )
            effect_manager.add_modifier(def_mod)

            import logging
            log = logging.getLogger(__name__)
            log.debug("Polished Shield resist bonus: +3 DEF for 1 turn to %s", target.id)
            payload = {
                "def_bonus": 3,
                "duration": 1,
                "trigger_event": "effect_resisted",
                "resisted_effect": effect_name,
            }
            if metadata:
                payload["metadata"] = metadata
            BUS.emit("card_effect", self.id, target, "resist_def_bonus", 3, payload)

        BUS.subscribe("effect_resisted", _on_effect_resisted)
