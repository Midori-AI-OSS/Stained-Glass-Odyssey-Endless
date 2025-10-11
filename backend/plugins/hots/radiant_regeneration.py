from autofighter.effects import HealingOverTime
from autofighter.stats import Stats


class RadiantRegeneration(HealingOverTime):
    plugin_type = "hot"
    # Include element in the id so frontends can infer visuals without extra metadata
    id = "light_radiant_regeneration"

    def __init__(self, source: Stats, *, turns: int = 2) -> None:
        base = max(15, int(source.atk * 0.2))
        healing = int(base * max(source.vitality, 1.0))
        super().__init__("Radiant Regeneration", healing, turns, self.id)
        self.source = source
