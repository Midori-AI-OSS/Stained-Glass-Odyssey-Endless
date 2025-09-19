from __future__ import annotations

from dataclasses import fields
from typing import Any
from typing import Collection
from typing import Mapping

from plugins.foes._base import FoeBase

from ..mapgen import MapNode
from ..party import Party
from ..passives import PassiveRegistry
from ..stats import GAUGE_START
from ..stats import Stats
from .foe_factory import get_foe_factory


def calculate_rank_probabilities(
    total_rooms_cleared: int = 0,
    floors_cleared: int = 0,
    pressure: int = 0,
) -> tuple[float, float]:
    """Proxy to the factory helper for rank progression odds."""

    factory = get_foe_factory()
    return factory.calculate_rank_probabilities(total_rooms_cleared, floors_cleared, pressure)


def _scale_stats(obj: Stats, node: MapNode, strength: float = 1.0) -> None:
    """Scale foe stats based on room metadata using the shared factory."""

    factory = get_foe_factory()
    factory.scale_stats(obj, node, strength)


def _choose_foe(node: MapNode, party: Party) -> FoeBase:
    """Select a single foe instance using the shared factory."""

    factory = get_foe_factory()
    foes = factory.build_encounter(node, party, exclude_ids=(), recent_ids=())
    if foes:
        return foes[0]
    fallback = next(iter(factory.templates.values()))
    return factory._instantiate(fallback).foe


def _get_effect_description(effect_name: str) -> str:
    """Get the description for an effect by its name."""
    try:
        if effect_name == "aftertaste":
            from plugins.effects.aftertaste import Aftertaste
            return Aftertaste.get_description()
        elif effect_name == "critical_boost":
            from plugins.effects.critical_boost import CriticalBoost
            return CriticalBoost.get_description()
        else:
            return "Unknown effect"
    except Exception:
        return "Unknown effect"


def _normalize_damage_type(dt: Any) -> str:
    """Return a simple identifier for a damage type or element."""
    try:
        if isinstance(dt, str):
            return dt
        ident = getattr(dt, "id", None) or getattr(dt, "name", None)
        if ident:
            return str(ident)
        if isinstance(dt, dict):
            return str(dt.get("id") or dt.get("name") or "Generic")
    except Exception:
        pass
    return "Generic"


def _serialize(obj: Stats) -> dict[str, Any]:
    """Convert a stat object into a plain serializable dictionary.

    This function is intentionally defensive: if an unexpected object is
    encountered (e.g., ``None``), it returns a minimal fallback to keep the
    battle snapshot and UI resilient instead of raising.
    """
    if obj is None:
        return {
            "id": "unknown",
            "name": "Unknown",
            "hp": 0,
            "max_hp": 0,
            "passives": [],
            "dots": [],
            "hots": [],
            "damage_type": "Generic",
            "element": "Generic",
            "level": 1,
            "atk": 0,
            "defense": 0,
            "mitigation": 100,
            "crit_rate": 0.0,
            "crit_damage": 2.0,
            "effect_hit_rate": 0.0,
            "effect_resistance": 0.0,
            "shields": 0,
            "overheal_enabled": False,
            "spd": 10,
            "action_gauge": GAUGE_START,
            "action_value": 0.0,
            "base_action_value": 0.0,
            "rank": "normal",
        }

    # Build a dict without dataclasses.asdict to avoid deepcopy of complex fields
    try:
        data: dict[str, Any] = {}
        for f in fields(type(obj)):
            name = f.name
            if name == "lrm_memory":
                continue
            value = getattr(obj, name, None)
            if isinstance(value, (int, float, bool, str)) or value is None:
                data[name] = value
            elif isinstance(value, list):
                data[name] = list(value)
            elif isinstance(value, dict):
                data[name] = dict(value)
            else:
                data[name] = str(value)
    except Exception:
        # Non-dataclass object or serialization issue: build a minimal view
        norm = _normalize_damage_type(getattr(obj, "damage_type", None))
        return {
            "id": getattr(obj, "id", "unknown"),
            "name": getattr(obj, "name", getattr(obj, "id", "Unknown")),
            "hp": int(getattr(obj, "hp", 0) or 0),
            "max_hp": int(getattr(obj, "max_hp", 0) or 0),
            "passives": [],
            "dots": [],
            "hots": [],
            "damage_type": norm,
            "element": norm,
            "level": int(getattr(obj, "level", 1) or 1),
            "atk": int(getattr(obj, "atk", 0) or 0),
            "defense": int(getattr(obj, "defense", 0) or 0),
            "mitigation": getattr(obj, "mitigation", 100) or 100,
            "crit_rate": float(getattr(obj, "crit_rate", 0.0) or 0.0),
            "crit_damage": float(getattr(obj, "crit_damage", 2.0) or 2.0),
            "effect_hit_rate": float(getattr(obj, "effect_hit_rate", 0.0) or 0.0),
            "effect_resistance": float(getattr(obj, "effect_resistance", 0.0) or 0.0),
            "shields": int(getattr(obj, "shields", 0) or 0),
            "overheal_enabled": bool(getattr(obj, "overheal_enabled", False)),
            "spd": int(getattr(obj, "spd", 10) or 10),
            "action_gauge": int(getattr(obj, "action_gauge", GAUGE_START) or GAUGE_START),
            "action_value": float(getattr(obj, "action_value", 0.0) or 0.0),
            "base_action_value": float(getattr(obj, "base_action_value", 0.0) or 0.0),
            "rank": getattr(obj, "rank", "normal"),
        }

    # Remove non-serializable fields introduced by plugins (e.g., runtime memory)
    data.pop("lrm_memory", None)
    norm = _normalize_damage_type(getattr(obj, "damage_type", None))
    data["damage_type"] = norm
    data["element"] = norm
    data["id"] = obj.id
    if hasattr(obj, "name"):
        data["name"] = obj.name
    if hasattr(obj, "char_type"):
        data["char_type"] = getattr(obj.char_type, "value", obj.char_type)
    data["rank"] = getattr(obj, "rank", "normal")

    data.pop("dots", None)
    data.pop("hots", None)
    registry = PassiveRegistry()
    data["passives"] = registry.describe(obj)

    mgr = getattr(obj, "effect_manager", None)
    dots = []
    hots = []
    if mgr is not None:
        def pack(effects, key):
            grouped: dict[str, dict[str, Any]] = {}
            for eff in effects:
                # Determine the elemental type for this effect from its source or attached type
                elem = "Generic"
                try:
                    src = getattr(eff, "source", None)
                    dtype = getattr(eff, "damage_type", None) or getattr(src, "damage_type", None)
                    elem = _normalize_damage_type(dtype)
                except Exception:
                    pass
                entry = grouped.setdefault(
                    eff.id,
                    {
                        "id": eff.id,
                        "name": eff.name,
                        key: getattr(eff, key),
                        "turns": eff.turns,
                        "source": getattr(getattr(eff, "source", None), "id", None),
                        "element": elem,
                        "stacks": 0,
                    },
                )
                entry["turns"] = max(entry["turns"], eff.turns)
                entry["stacks"] += 1
            return list(grouped.values())

        dots = pack(mgr.dots, "damage")
        hots = pack(mgr.hots, "healing")

    data["dots"] = dots
    data["hots"] = hots

    # Add special effects (aftertaste, crit boost, etc.)
    active_effects = []
    if hasattr(obj, '_active_effects'):
        for effect in obj.get_active_effects():
            active_effects.append({
                "name": effect.name,
                "source": effect.source,
                "duration": effect.duration,
                "modifiers": effect.stat_modifiers,
                "description": _get_effect_description(effect.name)
            })
    data["active_effects"] = active_effects

    # Ensure in-run (runtime) stats are present even when implemented as @property
    # on the Stats dataclass. For foes (plain dataclasses), fall back to raw attrs.
    def _num(get, default=0):
        try:
            v = get()
            return v if isinstance(v, (int, float)) else default
        except Exception:
            return default

    if isinstance(obj, Stats):
        data["max_hp"] = int(_num(lambda: obj.max_hp, data.get("max_hp", 0)))
        data["atk"] = int(_num(lambda: obj.atk, data.get("atk", 0)))
        data["defense"] = int(_num(lambda: obj.defense, data.get("defense", 0)))
        data["aggro"] = float(_num(lambda: obj.aggro, data.get("aggro", 0.0)))
        data["crit_rate"] = float(_num(lambda: obj.crit_rate, data.get("crit_rate", 0.0)))
        data["crit_damage"] = float(_num(lambda: obj.crit_damage, data.get("crit_damage", 2.0)))
        data["effect_hit_rate"] = float(_num(lambda: obj.effect_hit_rate, data.get("effect_hit_rate", 0.0)))
        data["effect_resistance"] = float(_num(lambda: obj.effect_resistance, data.get("effect_resistance", 0.0)))
        data["mitigation"] = float(_num(lambda: obj.mitigation, data.get("mitigation", 1.0)))
        data["vitality"] = float(_num(lambda: obj.vitality, data.get("vitality", 1.0)))
        data["regain"] = int(_num(lambda: obj.regain, data.get("regain", 0)))
        data["dodge_odds"] = float(_num(lambda: obj.dodge_odds, data.get("dodge_odds", 0.0)))
        # Add shields/overheal support
        data["shields"] = int(_num(lambda: getattr(obj, "shields", 0), 0))
        data["overheal_enabled"] = bool(getattr(obj, "overheal_enabled", False))
    else:
        # Non-Stats objects: keep provided values if present
        data.setdefault("max_hp", int(getattr(obj, "max_hp", data.get("max_hp", 0)) or 0))
        data.setdefault("atk", int(getattr(obj, "atk", data.get("atk", 0)) or 0))
        data.setdefault("defense", int(getattr(obj, "defense", data.get("defense", 0)) or 0))
        data.setdefault("aggro", float(getattr(obj, "aggro", data.get("aggro", 0.0)) or 0.0))
        data.setdefault("crit_rate", float(getattr(obj, "crit_rate", data.get("crit_rate", 0.0)) or 0.0))
        data.setdefault("crit_damage", float(getattr(obj, "crit_damage", data.get("crit_damage", 2.0)) or 2.0))
        data.setdefault("effect_hit_rate", float(getattr(obj, "effect_hit_rate", data.get("effect_hit_rate", 0.0)) or 0.0))
        data.setdefault("effect_resistance", float(getattr(obj, "effect_resistance", data.get("effect_resistance", 0.0)) or 0.0))
        data.setdefault("mitigation", float(getattr(obj, "mitigation", data.get("mitigation", 1.0)) or 1.0))
        data.setdefault("vitality", float(getattr(obj, "vitality", data.get("vitality", 1.0)) or 1.0))
        data.setdefault("regain", int(getattr(obj, "regain", data.get("regain", 0)) or 0))
        data.setdefault("dodge_odds", float(getattr(obj, "dodge_odds", data.get("dodge_odds", 0.0)) or 0.0))
        # Add shields/overheal support
        data.setdefault("shields", int(getattr(obj, "shields", 0) or 0))
        data.setdefault("overheal_enabled", bool(getattr(obj, "overheal_enabled", False)))

    return data


def _build_foes(
    node: MapNode,
    party: Party,
    *,
    exclude_ids: Collection[str] | None = None,
    recent_ids: Collection[str] | None = None,
    progression: Mapping[str, Any] | None = None,
) -> list[FoeBase]:
    factory = get_foe_factory()
    return factory.build_encounter(
        node,
        party,
        exclude_ids=exclude_ids or (),
        recent_ids=recent_ids or (),
        progression=progression or {},
    )
