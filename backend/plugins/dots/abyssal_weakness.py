from autofighter.effects import DamageOverTime
from autofighter.stat_effect import StatEffect


class AbyssalWeakness(DamageOverTime):
    plugin_type = "dot"
    id = "abyssal_weakness"

    def __init__(self, damage: int, turns: int) -> None:
        super().__init__("Abyssal Weakness", damage, turns, self.id)
        self._applied = False

    def tick(self, target, *_):
        if not self._applied:
            effect = StatEffect(
                name=f"{self.id}_defense_down",
                stat_modifiers={"defense": -1},
                source=self.id,
            )
            target.add_effect(effect)
            target.defense = max(target.defense, 0)
            self._applied = True
        active = super().tick(target)
        if not active:
            target.remove_effect_by_name(f"{self.id}_defense_down")
        return active
