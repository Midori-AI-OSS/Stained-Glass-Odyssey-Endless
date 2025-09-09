from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class GuardianShard(CardBase):
    id: str = "guardian_shard"
    name: str = "Guardian Shard"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"defense": 0.02, "mitigation": 0.02}
    )
