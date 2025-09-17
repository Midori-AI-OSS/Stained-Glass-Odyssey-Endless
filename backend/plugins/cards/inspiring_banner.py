from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class InspiringBanner(CardBase):
    id: str = "inspiring_banner"
    name: str = "Inspiring Banner"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.02, "defense": 0.02})
    about: str = "+2% ATK & +2% DEF; At battle start, grant a random ally +2% ATK for 2 turns"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        battle_started = False

        async def _on_battle_start(target):
            nonlocal battle_started
            # Only trigger once per battle and only when one of our party members starts
            if not battle_started and target in party.members:
                battle_started = True
                # Grant a random ally +2% ATK for 2 turns
                if party.members:
                    random_ally = random.choice(party.members)

                    effect_manager = getattr(random_ally, 'effect_manager', None)
                    if effect_manager is None:
                        effect_manager = EffectManager(random_ally)
                        random_ally.effect_manager = effect_manager

                    # Create temporary ATK buff
                    atk_mod = create_stat_buff(
                        random_ally,
                        name=f"{self.id}_battle_start",
                        turns=2,
                        atk_mult=1.02  # +2% ATK
                    )
                    effect_manager.add_modifier(atk_mod)

                    import logging
                    log = logging.getLogger(__name__)
                    log.debug("Inspiring Banner battle start: +2% ATK for 2 turns to %s", random_ally.id)
                    await BUS.emit_async("card_effect", self.id, random_ally, "battle_start_atk", 2, {
                        "atk_bonus": 2,
                        "duration": 2,
                        "trigger_event": "battle_start"
                    })

        BUS.subscribe("battle_start", _on_battle_start)