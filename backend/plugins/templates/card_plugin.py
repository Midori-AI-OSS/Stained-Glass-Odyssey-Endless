from dataclasses import dataclass, field
import logging

from plugins.cards._base import CardBase

log = logging.getLogger(__name__)


@dataclass
class SampleCard(CardBase):
    id: str = "sample_card"
    name: str = "Sample Card"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
