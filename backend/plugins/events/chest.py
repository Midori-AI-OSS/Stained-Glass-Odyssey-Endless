import random

from autofighter.events import Event
from autofighter.events import EventOption
from autofighter.stats import Stats


class ChestEvent:
    plugin_type = "event"
    id = "chest"

    @staticmethod
    def build(seed: int = 2) -> Event:
        async def _effect(
            stats: Stats, items: dict[str, int], rng: random.Random
        ) -> str:
            if rng.random() < 0.5:
                items["Upgrade Stone"] = items.get("Upgrade Stone", 0) + 1
                return "Inside you find an Upgrade Stone!"
            damage = rng.randint(1, 5)
            await stats.apply_damage(damage)
            return f"A trap! You take {damage} damage."

        return Event(
            "A dusty chest sits alone. Open it?",
            [
                EventOption("Open", _effect),
                EventOption("Ignore", lambda *_: "You move on."),
            ],
            seed=seed,
        )
