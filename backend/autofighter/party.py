from dataclasses import dataclass, field

from plugins.characters._base import PlayerBase


@dataclass
class Party:
    members: list[PlayerBase] = field(default_factory=list)
    gold: int = 0
    relics: list[str] = field(default_factory=list)
    cards: list[str] = field(default_factory=list)
    rdr: float = 1.0
    no_shops: bool = False
    no_rests: bool = False
    relic_persistent_state: dict[str, object] = field(default_factory=dict)
