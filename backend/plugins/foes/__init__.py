from __future__ import annotations

import random

from plugins import players as player_plugins
from plugins import themedadj as adj_plugins

from ._base import FoeBase

ADJ_CLASSES = [
    getattr(adj_plugins, name)
    for name in getattr(adj_plugins, "__all__", [])
]


def _wrap_player(cls: type) -> type[FoeBase]:
    class Wrapped(cls, FoeBase):
        plugin_type = "foe"

        def __post_init__(self) -> None:
            getattr(cls, "__post_init__", lambda self: None)(self)
            FoeBase.__post_init__(self)
            self.plugin_type = "foe"
            try:
                adj_cls = random.choice(ADJ_CLASSES)
                adj = adj_cls()
                adj.apply(self)
                self.name = f"{adj.name} {self.name}"
            except Exception:
                pass

    Wrapped.__name__ = f"{cls.__name__}Foe"
    return Wrapped


PLAYER_FOES: dict[str, type[FoeBase]] = {}
for name in getattr(player_plugins, "__all__", []):
    cls = getattr(player_plugins, name)
    foe_cls = _wrap_player(cls)
    PLAYER_FOES[cls.id] = foe_cls
    globals()[foe_cls.__name__] = foe_cls


__all__ = [cls.__name__ for cls in PLAYER_FOES.values()]

