from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class GuidingCompass(CardBase):
    id: str = "guiding_compass"
    name: str = "Guiding Compass"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"exp_multiplier": 0.03, "effect_hit_rate": 0.03})
    about: str = "+3% EXP Gain & +3% Effect Hit Rate; First battle of a run grants a small extra XP bonus"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        first_battle_bonus_used = False

        async def _on_battle_start(target, *_args):
            nonlocal first_battle_bonus_used
            # Only trigger once for the first battle of the run
            if not first_battle_bonus_used and target in party.members:
                first_battle_bonus_used = True
                # Grant extra XP bonus for all party members
                extra_xp = 10  # Small extra XP amount
                for member in party.members:
                    import logging

                    log = logging.getLogger(__name__)
                    log.debug(
                        "Guiding Compass first battle bonus: +%d XP to %s",
                        extra_xp,
                        member.id,
                    )
                    member.exp += extra_xp
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        member,
                        "first_battle_xp",
                        extra_xp,
                        {
                            "bonus_xp": extra_xp,
                            "trigger_event": "first_battle",
                        },
                    )

        BUS.subscribe("battle_start", _on_battle_start)

        async def _on_battle_end(*_args):
            nonlocal first_battle_bonus_used
            first_battle_bonus_used = False
            BUS.unsubscribe("battle_start", _on_battle_start)
            BUS.unsubscribe("battle_end", _on_battle_end)

        BUS.subscribe("battle_end", _on_battle_end)
