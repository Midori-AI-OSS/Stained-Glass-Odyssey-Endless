import logging
from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


log = logging.getLogger(__name__)


@dataclass
class GuidingCompass(CardBase):
    id: str = "guiding_compass"
    name: str = "Guiding Compass"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"exp_multiplier": 0.03, "effect_hit_rate": 0.03})
    about: str = "+3% EXP Gain & +3% Effect Hit Rate; First battle of a run grants a small extra XP bonus"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        flag_name = "guiding_compass_bonus_used"
        if not hasattr(party, flag_name):
            setattr(party, flag_name, False)

        async def _on_battle_start(target, *_args):
            if target not in party.members:
                return

            already_used = bool(getattr(party, flag_name, False))
            if already_used:
                return

            setattr(party, flag_name, True)

            extra_xp = 10  # Small extra XP amount
            for member in party.members:
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

        self.subscribe("battle_start", _on_battle_start)
