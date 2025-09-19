"""Passive plugin package bootstrap."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
import sys

__all__: list[str] = []


def _load_normal_passives() -> None:
    """Import normal passive modules and expose top-level aliases."""

    package_name = f"{__name__}.normal"
    package_path = Path(__file__).with_name("normal")

    if not package_path.exists():
        return

    for module_info in iter_modules([str(package_path)]):
        if module_info.name.startswith("_"):
            continue

        full_name = f"{package_name}.{module_info.name}"
        module = import_module(full_name)

        alias = f"{__name__}.{module_info.name}"
        sys.modules.setdefault(alias, module)
        globals()[module_info.name] = module
        __all__.append(module_info.name)


_load_normal_passives()
