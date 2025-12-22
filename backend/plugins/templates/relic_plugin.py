from dataclasses import dataclass, field
import logging

from plugins.relics._base import RelicBase

log = logging.getLogger(__name__)


@dataclass
class SampleRelic(RelicBase):
    id: str = "sample_relic"
    name: str = "Sample Relic"
    effects: dict[str, float] = field(default_factory=dict)
