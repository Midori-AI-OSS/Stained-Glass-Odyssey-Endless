from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from typing import Iterable
from typing import Mapping

from plugins.characters._base import PlayerBase


@dataclass(slots=True)
class PartyLoadoutCache:
    """Snapshot of party loadout used to avoid redundant stat refreshes."""

    card_ids: tuple[str, ...]
    relic_counts: Mapping[str, int]

    def matches(self, cards: Iterable[str], relics: Iterable[str]) -> bool:
        """Return ``True`` when cached loadout matches provided collections."""

        if tuple(cards) != self.card_ids:
            return False
        if Counter(relics) != Counter(self.relic_counts):
            return False
        return True


@dataclass
class Party:
    members: list[PlayerBase] = field(default_factory=list)
    gold: int = 0
    relics: list[str] = field(default_factory=list)
    cards: list[str] = field(default_factory=list)
    rdr: float = 1.0
    no_shops: bool = False
    no_rests: bool = False
    _loadout_cache: PartyLoadoutCache | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    def record_loadout_cache(self) -> None:
        """Persist the current cards and relic stacks for future battles."""

        self._loadout_cache = PartyLoadoutCache(
            card_ids=tuple(self.cards),
            relic_counts=dict(Counter(self.relics)),
        )

    def clear_loadout_cache(self) -> None:
        """Invalidate the cached loadout information."""

        self._loadout_cache = None
