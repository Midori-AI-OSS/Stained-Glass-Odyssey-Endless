from __future__ import annotations

from collections.abc import Iterable
import importlib
import pkgutil
import random

from plugins import themedadj as adj_plugins

from ._base import PlayerBase
from .foe_base import FoeBase


def _import_character_modules() -> Iterable[type[PlayerBase]]:
    characters: dict[str, type[PlayerBase]] = {}
    package_name = __name__
    for module_info in pkgutil.iter_modules(__path__):
        module_name = module_info.name
        if module_name.startswith("_") or module_name in {"foe_base"}:
            continue
        module = importlib.import_module(f"{package_name}.{module_name}")
        exported = getattr(module, "__all__", None)
        if exported is None:
            exported = [
                name
                for name, value in vars(module).items()
                if isinstance(value, type)
                and issubclass(value, PlayerBase)
                and value is not PlayerBase
            ]
        for name in exported:
            value = getattr(module, name, None)
            if not isinstance(value, type) or not issubclass(value, PlayerBase):
                continue
            if value is PlayerBase:
                continue
            globals()[name] = value
            characters[value.__name__] = value
    return characters.values()


_CHARACTER_EXPORTS: tuple[type[PlayerBase], ...] = tuple(_import_character_modules())

ADJ_CLASSES = [
    getattr(adj_plugins, name)
    for name in getattr(adj_plugins, "__all__", [])
]


def _wrap_character(cls: type[PlayerBase]) -> type[FoeBase]:
    class Wrapped(cls, FoeBase):
        plugin_type = "foe"

        def __post_init__(self) -> None:  # type: ignore[override]
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


CHARACTER_FOES: dict[str, type[FoeBase]] = {}
for _character in _CHARACTER_EXPORTS:
    if not hasattr(_character, "id"):
        continue
    foe_cls = _wrap_character(_character)
    CHARACTER_FOES[_character.id] = foe_cls
    globals()[foe_cls.__name__] = foe_cls

_PLAYABLE_EXPORTS = tuple(cls.__name__ for cls in _CHARACTER_EXPORTS)
_FOE_EXPORTS = tuple(foe_cls.__name__ for foe_cls in CHARACTER_FOES.values())


__all__ = list(_PLAYABLE_EXPORTS + _FOE_EXPORTS)
