from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class EnergizingTea(CardBase):
    id: str = "energizing_tea"
    name: str = "Energizing Tea"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"regain": 0.03})
    about: str = "+3% Regain; At battle start, gain +1 ultimate charge on the first turn"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        battle_started = False

        async def _on_battle_start(target):
            nonlocal battle_started
            # Only trigger once per battle and only for party members
            if not battle_started and target in party.members:
                battle_started = True
                # Give +1 ultimate charge to all party members
                for member in party.members:
                    member.add_ultimate_charge(1)
                    import logging
                    log = logging.getLogger(__name__)
                    log.debug("Energizing Tea bonus ultimate charge: +1 charge to %s", member.id)
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        member,
                        "charge_bonus",
                        1,
                        {
                            "charge_bonus": 1,
                            "trigger_event": "battle_start",
                        },
                    )

                BUS.unsubscribe("battle_start", _on_battle_start)
                BUS.unsubscribe("battle_end", _on_battle_end)

        def _on_battle_end(entity) -> None:
            BUS.unsubscribe("battle_start", _on_battle_start)
            BUS.unsubscribe("battle_end", _on_battle_end)

        BUS.subscribe("battle_start", _on_battle_start)
        BUS.subscribe("battle_end", _on_battle_end)
