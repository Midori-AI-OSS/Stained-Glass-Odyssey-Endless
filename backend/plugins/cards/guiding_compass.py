from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.stats import BUS
from plugins.cards._base import CardBase

log = logging.getLogger(__name__)


@dataclass
class GuidingCompass(CardBase):
    id: str = "guiding_compass"
    name: str = "Guiding Compass"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"exp_multiplier": 0.03, "effect_hit_rate": 0.03})
    full_about: str = (
        "+3% EXP Gain & +3% Effect Hit Rate; grants a one-time full level up to all party members when acquired."
    )
    summarized_about: str = (
        "Boosts exp gain and effect hit rate; grants instant level up when acquired"
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        flag_name = "guiding_compass_level_up_awarded"
        if getattr(party, flag_name, False):
            return

        setattr(party, flag_name, True)

        for member in party.members:
            previous_level = getattr(member, "level", 0)
            member.level = previous_level + 1
            log.debug(
                "Guiding Compass instant level up applied to %s (level %d -> %d)",
                getattr(member, "id", "member"),
                previous_level,
                member.level,
            )

            member._on_level_up()

            await member._trigger_level_up_passives()

            await BUS.emit_async(
                "card_effect",
                self.id,
                member,
                "instant_level_up",
                member.level,
                {
                    "trigger_event": "card_pickup",
                    "new_level": member.level,
                    "previous_level": previous_level,
                },
            )
