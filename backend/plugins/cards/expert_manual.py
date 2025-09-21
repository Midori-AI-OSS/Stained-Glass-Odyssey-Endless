from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class ExpertManual(CardBase):
    id: str = "expert_manual"
    name: str = "Expert Manual"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"exp_multiplier": 0.03})
    about: str = "+3% EXP Gain; 5% chance to give a small extra XP on a kill once per battle"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        extra_xp_used = set()

        async def _on_kill(target, killer, damage, death_type, details):
            # Check if killer is one of our party members
            if killer in party.members:
                killer_id = id(killer)
                # 5% chance to give extra XP, once per battle
                if killer_id not in extra_xp_used and random.random() < 0.05:
                    extra_xp_used.add(killer_id)
                    # Grant small extra XP
                    extra_xp = 5  # Small extra XP amount
                    killer.exp += extra_xp
                    import logging
                    log = logging.getLogger(__name__)
                    log.debug("Expert Manual bonus XP: +%d XP to %s", extra_xp, killer.id)
                    await BUS.emit_async("card_effect", self.id, killer, "bonus_xp", extra_xp, {
                        "bonus_xp": extra_xp,
                        "trigger_chance": 0.05,
                        "trigger_event": "kill"
                    })

        def _on_battle_start(target):
            # Reset extra XP usage for new battle
            if target in party.members:
                extra_xp_used.clear()

        self.subscribe("entity_killed", _on_kill)
        self.subscribe("battle_start", _on_battle_start)
