from autofighter.effects import DamageOverTime


class AbyssalCorruption(DamageOverTime):
    plugin_type = "dot"
    id = "abyssal_corruption"

    def __init__(self, damage: int, turns: int) -> None:
        super().__init__("Abyssal Corruption", damage, turns, self.id)

    async def on_death(self, target_manager) -> None:
        await target_manager.add_dot(AbyssalCorruption(self.damage, self.turns))
