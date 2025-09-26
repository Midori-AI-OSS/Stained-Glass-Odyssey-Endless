"""Plugin discovery helpers for foe spawn templates."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Callable
from typing import Collection
from typing import Iterable

from plugins import characters as character_plugins
from plugins.characters.foe_base import FoeBase
from plugins.plugin_loader import PluginLoader

if TYPE_CHECKING:
    from autofighter.mapgen import MapNode


@dataclass(frozen=True)
class SpawnTemplate:
    """Metadata describing a foe spawn template."""

    id: str
    cls: type[FoeBase]
    tags: frozenset[str] = field(default_factory=frozenset)
    weight_hook: Callable[[MapNode, Collection[str], Collection[str] | None, bool], float] | None = None
    base_rank: str = "normal"
    apply_adjective: bool = False


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[3] / "plugins"


def _safe_get_plugins(loader: PluginLoader, category: str) -> dict[str, type]:
    try:
        return loader.get_plugins(category)
    except Exception:
        return {}


def _wrap_player(cls: type) -> type[FoeBase]:
    base_rank = getattr(cls, "rank", "normal")

    class Wrapped(cls, FoeBase):  # type: ignore[misc, valid-type]
        plugin_type = "foe"
        rank = base_rank

        def __post_init__(self) -> None:  # noqa: D401 - thin wrapper
            getattr(cls, "__post_init__", lambda self: None)(self)
            FoeBase.__post_init__(self)
            self.plugin_type = "foe"

    Wrapped.__name__ = f"{cls.__name__}Foe"
    return Wrapped


def _is_base_class(cls: type) -> bool:
    module_name = getattr(cls, "__module__", "")
    return module_name.endswith("._base") or module_name.endswith(".foe_base")


def load_catalog() -> tuple[dict[str, SpawnTemplate], dict[str, SpawnTemplate], list[type]]:
    """Discover combatant plugins and build spawn templates."""

    loader = PluginLoader()
    root = _plugin_root()
    for category in ("characters", "themedadj"):
        loader.discover(str(root / category))

    foes = _safe_get_plugins(loader, "foe")
    players = _safe_get_plugins(loader, "player")
    adjectives = _safe_get_plugins(loader, "themedadj")

    # Ensure dynamically wrapped character foes are visible to the registry
    for ident, foe_cls in getattr(character_plugins, "CHARACTER_FOES", {}).items():
        foes.setdefault(ident, foe_cls)

    templates: dict[str, SpawnTemplate] = {}
    player_templates: dict[str, SpawnTemplate] = {}

    for foe_cls in foes.values():
        if _is_base_class(foe_cls):
            continue
        ident = getattr(foe_cls, "id", foe_cls.__name__)
        tags: Iterable[str] = getattr(foe_cls, "spawn_tags", ()) or ()
        hook = getattr(foe_cls, "get_spawn_weight", None)
        templates[ident] = SpawnTemplate(
            id=ident,
            cls=foe_cls,
            tags=frozenset(tags),
            weight_hook=hook,
            base_rank=getattr(foe_cls, "rank", "normal"),
        )

    character_wrappers = getattr(character_plugins, "CHARACTER_FOES", {})

    for player_cls in players.values():
        if _is_base_class(player_cls):
            continue
        ident = getattr(player_cls, "id", player_cls.__name__)
        wrapper = character_wrappers.get(ident) or _wrap_player(player_cls)
        hook = getattr(player_cls, "get_spawn_weight", None)
        existing = templates.get(ident)
        tags = set(getattr(wrapper, "spawn_tags", ()) or ())
        if existing is not None:
            tags.update(existing.tags)
        tags.add("player_template")
        template = SpawnTemplate(
            id=ident,
            cls=wrapper,
            tags=frozenset(tags),
            weight_hook=hook or (existing.weight_hook if existing else None),
            base_rank=getattr(wrapper, "rank", getattr(player_cls, "rank", "normal")),
            apply_adjective=True,
        )
        templates[ident] = template
        player_templates[ident] = template

    adjective_types = list(adjectives.values())
    return templates, player_templates, adjective_types
