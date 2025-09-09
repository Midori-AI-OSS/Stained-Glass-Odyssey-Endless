from autofighter.effects import DamageOverTime
from autofighter.effects import StatModifier
from autofighter.effects import create_stat_buff


class CelestialAtrophy(DamageOverTime):
    plugin_type = "dot"
    id = "celestial_atrophy"

    def __init__(self, damage: int, turns: int) -> None:
        super().__init__("Celestial Atrophy", damage, turns, self.id)
        self._mods: list[StatModifier] = []

    async def tick(self, target, *_):
        manager = getattr(target, "effect_manager", None)
        if manager is not None:
            mod = create_stat_buff(
                target,
                name="Celestial Atrophy - Attack Down",
                id=f"{self.id}_atk_down",
                turns=self.turns,
                atk=-1,
            )
            manager.add_modifier(mod)
            self._mods.append(mod)
        alive = await super().tick(target)
        if not alive and manager is not None:
            for mod in reversed(self._mods):
                mod.remove()
                if mod in manager.mods:
                    manager.mods.remove(mod)
                if mod.id in target.mods:
                    target.mods.remove(mod.id)
            self._mods.clear()
        return alive
