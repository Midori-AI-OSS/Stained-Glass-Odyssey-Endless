from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Mapping

from autofighter.stat_effect import StatEffect
from plugins import PluginLoader

if TYPE_CHECKING:
    from autofighter.stats import Stats
    from plugins.effects import BuffBase


_loader: PluginLoader | None = None
_REGISTRY: dict[str, type["BuffBase"]] | None = None


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1] / "plugins" / "effects" / "buffs"


def discover() -> dict[str, type["BuffBase"]]:
    """Load buff plugins exactly once and return the registry."""

    global _loader
    global _REGISTRY

    if _REGISTRY is None:
        root = _plugin_root()
        _loader = PluginLoader(required=["buff"])
        _loader.discover(str(root))
        _REGISTRY = _loader.get_plugins("buff")
    return _REGISTRY


class BuffRegistry:
    """Runtime helper that exposes buff plugin classes and application helpers."""

    def __init__(self) -> None:
        self._registry = discover()

    def register(self, buff_id: str, buff_class: type["BuffBase"]) -> None:
        self._registry[buff_id] = buff_class

    def get_buff(self, buff_id: str) -> type["BuffBase"] | None:
        return self._registry.get(buff_id)

    def all_buffs(self) -> dict[str, type["BuffBase"]]:
        return dict(self._registry)

    async def apply_buff(
        self,
        buff_id: str,
        target: "Stats",
        *,
        init_kwargs: Mapping[str, object] | None = None,
        **apply_kwargs: object,
    ) -> StatEffect:
        buff_cls = self.get_buff(buff_id)
        if buff_cls is None:
            raise KeyError(f"Unknown buff '{buff_id}'")
        init_args = dict(init_kwargs or {})
        buff = buff_cls(**init_args)
        return await buff.apply(target, **apply_kwargs)
