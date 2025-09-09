from __future__ import annotations

from pathlib import Path

from autofighter.effects import create_stat_buff
from plugins import PluginLoader


def stat_buff(cls):
    """Wrap adjective apply methods to attach a lasting stat buff."""

    original = cls.apply

    def apply(self, target) -> None:  # type: ignore[override]
        base_atk = getattr(target, "atk", None)
        base_def = getattr(target, "defense", None)
        base_hp = getattr(target, "max_hp", None)

        original(self, target)

        mults = {}
        if base_atk is not None and target.atk != base_atk:
            mults["atk_mult"] = target.atk / base_atk
            target.atk = base_atk
        if base_def is not None and target.defense != base_def:
            mults["defense_mult"] = target.defense / base_def
            target.defense = base_def
        if base_hp is not None and target.max_hp != base_hp:
            mults["max_hp_mult"] = target.max_hp / base_hp
            target.max_hp = base_hp

        if mults:
            effect = create_stat_buff(
                target,
                name=getattr(self, "name", "buff"),
                id=getattr(self, "id", "stat_buff"),
                turns=9999,
                **mults,
            )
            mgr = getattr(target, "effect_manager", None)
            if mgr is not None:
                mgr.add_modifier(effect)
            else:
                pending = getattr(target, "_pending_mods", [])
                pending.append(effect)
                target._pending_mods = pending

    cls.apply = apply
    return cls


loader = PluginLoader()
loader.discover(str(Path(__file__).resolve().parent))
_plugins = loader.get_plugins("themedadj")

for cls in _plugins.values():
    globals()[cls.__name__] = cls

__all__ = sorted(cls.__name__ for cls in _plugins.values())
