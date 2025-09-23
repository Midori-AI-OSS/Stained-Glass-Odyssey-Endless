from __future__ import annotations

from pathlib import Path

from autofighter.rooms.foes.scaling import apply_permanent_scaling
from plugins import PluginLoader


def stat_buff(cls):
    """Wrap adjective apply methods to attach a lasting stat buff."""

    original = cls.apply

    def apply(self, target) -> None:  # type: ignore[override]
        base_atk = getattr(target, "atk", None)
        base_def = getattr(target, "defense", None)
        base_hp = getattr(target, "max_hp", None)

        original(self, target)

        mults: dict[str, float] = {}
        additive: dict[str, float] = {}

        if base_atk is not None and target.atk != base_atk:
            if base_atk:
                mults["atk"] = target.atk / base_atk
            else:
                additive["atk"] = target.atk - base_atk
            target.atk = base_atk
        if base_def is not None and target.defense != base_def:
            if base_def:
                mults["defense"] = target.defense / base_def
            else:
                additive["defense"] = target.defense - base_def
            target.defense = base_def
        if base_hp is not None and target.max_hp != base_hp:
            if base_hp:
                mults["max_hp"] = target.max_hp / base_hp
            else:
                additive["max_hp"] = target.max_hp - base_hp
            target.max_hp = base_hp

        if mults or additive:
            apply_permanent_scaling(
                target,
                multipliers=mults or None,
                deltas=additive or None,
                name=getattr(self, "name", "buff"),
                modifier_id=getattr(self, "id", "stat_buff"),
            )

    cls.apply = apply
    return cls


loader = PluginLoader()
loader.discover(str(Path(__file__).resolve().parent))
_plugins = loader.get_plugins("themedadj")

for cls in _plugins.values():
    globals()[cls.__name__] = cls

__all__ = sorted(cls.__name__ for cls in _plugins.values())

