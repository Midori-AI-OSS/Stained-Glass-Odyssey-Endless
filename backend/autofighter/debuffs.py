from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Mapping

from autofighter.stat_effect import StatEffect
from plugins import PluginLoader

if TYPE_CHECKING:
    from autofighter.stats import Stats
    from plugins.effects import DebuffBase


_loader: PluginLoader | None = None
_REGISTRY: dict[str, type["DebuffBase"]] | None = None


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1] / "plugins" / "effects" / "debuffs"


def discover() -> dict[str, type["DebuffBase"]]:
    """Load debuff plugins exactly once and return the registry."""

    global _loader
    global _REGISTRY

    if _REGISTRY is None:
        root = _plugin_root()
        _loader = PluginLoader(required=["debuff"])
        _loader.discover(str(root))
        _REGISTRY = _loader.get_plugins("debuff")
    return _REGISTRY


class DebuffRegistry:
    """Runtime helper that exposes debuff plugin classes and application helpers."""

    def __init__(self) -> None:
        self._registry = discover()

    def register(self, debuff_id: str, debuff_class: type["DebuffBase"]) -> None:
        self._registry[debuff_id] = debuff_class

    def get_debuff(self, debuff_id: str) -> type["DebuffBase"] | None:
        return self._registry.get(debuff_id)

    def all_debuffs(self) -> dict[str, type["DebuffBase"]]:
        return dict(self._registry)

    async def apply_debuff(
        self,
        debuff_id: str,
        target: "Stats",
        *,
        init_kwargs: Mapping[str, object] | None = None,
        **apply_kwargs: object,
    ) -> StatEffect:
        debuff_cls = self.get_debuff(debuff_id)
        if debuff_cls is None:
            raise KeyError(f"Unknown debuff '{debuff_id}'")
        init_args = dict(init_kwargs or {})
        debuff = debuff_cls(**init_args)
        return await debuff.apply(target, **apply_kwargs)
