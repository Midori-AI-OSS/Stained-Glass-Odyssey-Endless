from dataclasses import dataclass
from dataclasses import field
import logging
import math

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class MindfulTassel(CardBase):
    id: str = "mindful_tassel"
    name: str = "Mindful Tassel"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"effect_hit_rate": 0.03})
    about: str = "+3% Effect Hit Rate; First debuff applied each battle has +5% potency"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        bonus_used = False

        async def _on_effect_applied(effect_name, entity, details=None):
            nonlocal bonus_used

            if bonus_used or not details:
                return

            effect_id = details.get("effect_id")
            effect_type = details.get("effect_type")
            if effect_id is None or effect_type not in {"dot", "stat_modifier"}:
                return

            if effect_type == "stat_modifier":
                deltas = details.get("deltas") or {}
                multipliers = details.get("multipliers") or {}
                if not any(v < 0 for v in deltas.values()) and not any(
                    v < 1 for v in multipliers.values()
                ):
                    return

            mgr = getattr(entity, "effect_manager", None)
            if mgr is None:
                return

            if effect_type == "dot":
                pool = mgr.dots
            else:
                pool = mgr.mods

            eff = next((e for e in pool if getattr(e, "id", None) == effect_id), None)
            if eff is None:
                return

            source = getattr(eff, "source", None)
            if source not in party.members:
                return

            bonus_used = True

            if hasattr(eff, "damage"):
                eff.damage = int(eff.damage * 1.05)

            if hasattr(eff, "turns") and eff.turns > 0:
                eff.turns = max(eff.turns, math.ceil(eff.turns * 1.05))

            log = logging.getLogger(__name__)
            log.debug(
                "Mindful Tassel first debuff potency: +5% potency to %s",
                effect_name,
            )
            await BUS.emit_async(
                "card_effect",
                self.id,
                source,
                "debuff_potency_boost",
                5,
                {
                    "potency_boost": 5,
                    "effect_name": effect_name,
                    "trigger_event": "first_debuff",
                },
            )

        def _on_battle_start(entity):
            nonlocal bonus_used
            if entity in party.members:
                bonus_used = False

        def _on_battle_end(_entity) -> None:
            BUS.unsubscribe("effect_applied", _on_effect_applied)
            BUS.unsubscribe("battle_start", _on_battle_start)
            BUS.unsubscribe("battle_end", _on_battle_end)

        BUS.subscribe("effect_applied", _on_effect_applied)
        BUS.subscribe("battle_start", _on_battle_start)
        BUS.subscribe("battle_end", _on_battle_end)