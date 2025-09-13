from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class SwiftFootwork(CardBase):
    id: str = "swift_footwork"
    name: str = "Swift Footwork"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "+1 action per turn; first action each combat is free."

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)
        for member in party.members:
            member.actions_per_turn += 1

        used: set[int] = set()

        def _battle_start(entity) -> None:
            used.clear()

        def _action_used(actor, *_args) -> None:
            if actor not in party.members:
                return

            pid = id(actor)
            if pid in used:
                return

            actor.action_points += 1
            BUS.emit("extra_turn", actor)
            used.add(pid)
            BUS.emit("card_effect", self.id, actor, "free_action", 0, {})

        BUS.subscribe("battle_start", _battle_start)
        BUS.subscribe("action_used", _action_used)
