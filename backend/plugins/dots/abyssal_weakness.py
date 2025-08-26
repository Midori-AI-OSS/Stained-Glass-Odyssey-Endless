from autofighter.effects import DamageOverTime


class AbyssalWeakness(DamageOverTime):
    plugin_type = "dot"
    id = "abyssal_weakness"

    def __init__(self, damage: int, turns: int) -> None:
        super().__init__("Abyssal Weakness", damage, turns, self.id)
        self._applied = False

    def tick(self, target, *_):
        if not self._applied:
            target.adjust_stat_on_loss("defense", 1)
            target.defense = max(target.defense, 0)
            self._applied = True
        alive = super().tick(target)
        if not alive:
            target.adjust_stat_on_gain("defense", 1)
        return alive
