from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from dataclasses import field
from importlib import import_module
from pkgutil import iter_modules
from typing import Any

from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task
from plugins.damage_effects import DOT_FACTORIES
import plugins.dots as dots_pkg


def _collect_dot_ids() -> frozenset[str]:
    dot_ids: set[str] = set()
    for _finder, module_name, is_package in iter_modules(getattr(dots_pkg, "__path__", [])):
        if is_package or module_name.startswith("_"):
            continue
        module = None
        with suppress(Exception):
            module = import_module(f"{dots_pkg.__name__}.{module_name}")
        if module is None:
            continue
        for value in vars(module).values():
            if getattr(value, "plugin_type", None) != "dot":
                continue
            plugin_id = getattr(value, "id", None)
            if isinstance(plugin_id, str):
                dot_ids.add(plugin_id)
    return frozenset(dot_ids)


_KNOWN_DOT_DAMAGE_TYPES = frozenset(DOT_FACTORIES)
_KNOWN_DOT_IDS = _collect_dot_ids()


@dataclass
class MysticAegis(CardBase):
    id: str = "mystic_aegis"
    name: str = "Mystic Aegis"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=lambda: {"effect_resistance": 0.55})
    about: str = "+55% Effect Res; when an ally resists a debuff, they heal for 5% Max HP."

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _resisted(effect_name, target, source, details=None) -> None:
            if target is None or target not in party.members:
                return
            metadata: Mapping[str, Any] = details if isinstance(details, Mapping) else {}
            effect_type = metadata.get("effect_type")
            is_debuff = False

            if effect_type == "stat_modifier":
                deltas = metadata.get("deltas") or {}
                multipliers = metadata.get("multipliers") or {}
                has_negative_delta = any(
                    isinstance(value, (int, float)) and value < 0 for value in deltas.values()
                )
                has_reductive_multiplier = any(
                    isinstance(value, (int, float)) and value < 1 for value in multipliers.values()
                )
                is_debuff = has_negative_delta or has_reductive_multiplier
            elif effect_type == "dot":
                damage_type = metadata.get("damage_type")
                effect_id = metadata.get("effect_id")
                is_known_damage_type = isinstance(damage_type, str) and damage_type in _KNOWN_DOT_DAMAGE_TYPES
                is_known_dot = isinstance(effect_id, str) and effect_id in _KNOWN_DOT_IDS
                is_debuff = is_known_damage_type or is_known_dot
            elif effect_type == "debuff":
                is_debuff = True
            elif metadata.get("is_debuff") is True:
                is_debuff = True

            if not is_debuff:
                return

            heal = int(target.max_hp * 0.05)
            await BUS.emit_async(
                "card_effect",
                self.id,
                target,
                "healing",
                heal,
                {"heal_amount": heal},
            )
            safe_async_task(target.apply_healing(heal))

        self.subscribe("effect_resisted", _resisted)
