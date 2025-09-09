import random

from autofighter.events import Event
from autofighter.events import EventOption
from autofighter.stats import Stats


class FountainEvent:
    plugin_type = "event"
    id = "fountain"

    @staticmethod
    def build(seed: int = 1) -> Event:
        async def _effect(
            stats: Stats, _items: dict[str, int], rng: random.Random
        ) -> str:
            heal = rng.randint(5, 10)
            await stats.apply_healing(heal)
            return f"You feel restored: +{heal} HP"

        return Event(
            "A shimmering fountain beckons. Drink?",
            [
                EventOption("Drink", _effect),
                EventOption("Leave", lambda *_: "You walk away."),
            ],
            seed=seed,
        )
