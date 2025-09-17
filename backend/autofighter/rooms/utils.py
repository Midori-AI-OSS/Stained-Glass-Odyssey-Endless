from __future__ import annotations

from dataclasses import fields
import math
import random
from typing import Any

from plugins import foes as foe_plugins
from plugins import players as player_plugins
from plugins.foes._base import FoeBase

from ..mapgen import MapNode
from ..party import Party
from ..passives import PassiveRegistry
from ..stats import GAUGE_START
from ..stats import Stats

# Action caps for foes to prevent runaway turn economy
FOE_MAX_ACTIONS_PER_TURN: int = 1     # 1 action per turn
FOE_MAX_ACTION_POINTS: int = 1        # start and cap at very low AP


def _scale_stats(obj: Stats, node: MapNode, strength: float = 1.0) -> None:
    """Scale foe stats based on room metadata.

    Foes grow stronger with cumulative room progression across floors, loop count, and user-set pressure.
    Each floor adds 10 rooms worth of stat progression (rooms_per_floor from MapGenerator).
    Small per-stat variation keeps battles from feeling identical.
    """
    from ..mapgen import MapGenerator

    starter_int = 1.0 + random.uniform(-0.05, 0.05)
    # Calculate cumulative room progression: (floors - 1) * rooms_per_floor + current_room_index
    cumulative_rooms = (node.floor - 1) * MapGenerator.rooms_per_floor + node.index
    room_mult = starter_int + 0.85 * max(cumulative_rooms - 1, 0)
    loop_mult = starter_int + 1.30 * max(node.loop - 1, 0)
    pressure_mult = 1.0 * max(node.pressure, 1)
    base_mult = max(strength * room_mult * loop_mult * pressure_mult, 0.5)

    # Apply a global pre-scale debuff to foes so they are significantly weaker
    # before room modifiers are applied.
    foe_debuff = 0.5 if isinstance(obj, FoeBase) else 1.0
    if foe_debuff != 1.1:
        try:
            if hasattr(obj, "atk") and isinstance(obj.atk, (int, float)):
                obj.atk = type(obj.atk)(obj.atk * foe_debuff)
        except Exception:
            pass
        try:
            if hasattr(obj, "defense") and isinstance(obj.defense, (int, float)):
                obj.defense = type(obj.defense)(obj.defense * min((foe_debuff * node.floor) / 4, 1))
        except Exception:
            pass
        try:
            if hasattr(obj, "max_hp") and isinstance(obj.max_hp, (int, float)):
                obj.max_hp = type(obj.max_hp)(obj.max_hp * foe_debuff)
            if hasattr(obj, "hp") and isinstance(obj.hp, (int, float)):
                obj.hp = type(obj.hp)(obj.hp * foe_debuff)
        except Exception:
            pass

    for field in fields(type(obj)):
        if field.name in {"exp", "level", "exp_multiplier"}:
            continue
        value = getattr(obj, field.name, None)
        if isinstance(value, (int, float)):
            per_stat_variation = 1.0 + random.uniform(-0.05, 0.05)
            total = value * base_mult * per_stat_variation
            setattr(obj, field.name, type(value)(total))

    try:
        room_num = max(int(cumulative_rooms), 1)
        desired = max(1, math.ceil(room_num / 2))
        obj.level = int(max(getattr(obj, "level", 1), desired))
    except Exception:
        pass

    try:
        room_num = max(int(node.index), 1)
        # Keep the same base curve but apply foe debuff to the minimum target as well
        base_hp = int(15 * room_num * (foe_debuff if isinstance(obj, FoeBase) else 1.0))
        low = int(base_hp * 0.85)
        high = int(base_hp * 1.10)
        target = random.randint(low, max(high, low + 1))
        current_max = int(getattr(obj, "max_hp", 1))
        new_max = max(current_max, target)
        obj.max_hp = new_max
        obj.hp = new_max
    except Exception:
        pass

    try:
        cd = getattr(obj, "crit_damage", None)
        if isinstance(cd, (int, float)):
            obj.crit_damage = type(cd)(max(float(cd), 2.0))
    except Exception:
        pass

    # Apply post-scale clamps for foes' action economy
    if isinstance(obj, FoeBase):
        try:
            er = getattr(obj, "effect_resistance", None)
            if isinstance(er, (int, float)):
                obj.effect_resistance = float(max(0.0, er))
        except Exception:
            pass
        try:
            apt = getattr(obj, "actions_per_turn", None)
            if isinstance(apt, (int, float)):
                obj.actions_per_turn = int(min(max(1, int(apt)), FOE_MAX_ACTIONS_PER_TURN))
        except Exception:
            pass
        try:
            ap = getattr(obj, "action_points", None)
            if isinstance(ap, (int, float)):
                obj.action_points = int(min(max(0, int(ap)), FOE_MAX_ACTION_POINTS))
        except Exception:
            pass

    # Enforce a minimum defense value for foes so they are not trivially zeroed.
    try:
        if isinstance(obj, FoeBase):
            d = getattr(obj, "defense", None)
            if isinstance(d, (int, float)):
                override = getattr(obj, "min_defense_override", None)
                if isinstance(override, (int, float)):
                    min_def = max(int(override), 0)
                else:
                    min_def = 2 + cumulative_rooms

                new_def = max(min_def, int(d))
                # For foes, 'defense' is a dataclass field; set the field directly
                try:
                    setattr(obj, "defense", type(d)(new_def))
                except Exception:
                    # As a fallback, adjust base stat
                    try:
                        obj.set_base_stat("defense", new_def)
                    except Exception:
                        pass
    except Exception:
        pass

    # Apply pressure-based defense scaling for foes with randomness
    try:
        if isinstance(obj, FoeBase) and node.pressure > 0:
            d = getattr(obj, "defense", None)
            if isinstance(d, (int, float)):
                # Calculate pressure-based defense: pressure * 10 with randomness
                # For pressure=5: target 41-75 (base 50 with range -18% to +50%)
                pressure_base_def = node.pressure * 10
                min_factor = 0.82  # -18% (50 * 0.82 = 41)
                max_factor = 1.50  # +50% (50 * 1.50 = 75)
                random_factor = random.uniform(min_factor, max_factor)
                pressure_defense = int(pressure_base_def * random_factor)

                # Set the defense to be at least the pressure-based value
                # but also respect any higher value from other scaling
                current_def = int(d)
                final_defense = max(current_def, pressure_defense)

                try:
                    setattr(obj, "defense", type(d)(final_defense))
                except Exception:
                    # As a fallback, adjust base stat
                    try:
                        obj.set_base_stat("defense", final_defense)
                    except Exception:
                        pass
    except Exception:
        pass

    try:
        if isinstance(obj, FoeBase):
            vit = getattr(obj, "vitality", None)
            if isinstance(vit, (int, float)):
                thr = 0.5
                step = 0.25
                base_slow = 5.0
                fvit = float(vit)
                if fvit < thr:
                    fvit = thr
                else:
                    excess = fvit - thr
                    steps = int(excess // step)
                    factor = base_slow + steps
                    fvit = thr + (excess / factor)
                    fvit = max(fvit, thr)
                # Foes use dataclass fields, so set the live field directly
                try:
                    setattr(obj, "vitality", type(vit)(fvit))
                except Exception:
                    pass
    except Exception:
        pass

    try:
        if isinstance(obj, FoeBase):
            mit = getattr(obj, "mitigation", None)
            if isinstance(mit, (int, float)):
                thr = 0.2
                step = 0.01
                base_slow = 5.0
                fmit = float(mit)
                if fmit < thr:
                    fmit = thr
                else:
                    excess = fmit - thr
                    steps = int(excess // step)
                    factor = base_slow + steps
                    fmit = thr + (excess / factor)
                    fmit = max(fmit, thr)
                # Foes use dataclass fields, so set the live field directly
                try:
                    setattr(obj, "mitigation", type(mit)(fmit))
                except Exception:
                    pass
    except Exception:
        pass


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


def _choose_foe(party: Party) -> FoeBase:
    """Select a foe class not already in the party."""
    party_ids = {p.id for p in party.members}
    candidates = [
        getattr(foe_plugins, name)
        for name in getattr(foe_plugins, "__all__", [])
        if getattr(foe_plugins, name).id not in party_ids
    ]
    for name in getattr(player_plugins, "__all__", []):
        player_cls = getattr(player_plugins, name)
        if player_cls.id in party_ids:
            continue
        foe_cls = foe_plugins.PLAYER_FOES.get(player_cls.id)
        if foe_cls and foe_cls not in candidates:
            candidates.append(foe_cls)
    if not candidates:
        candidates = [foe_plugins.Slime]
    weights = [
        3 if getattr(cls, "id", None) == "luna" and "luna" not in party_ids else 1
        for cls in candidates
    ]
    foe_cls = random.choices(candidates, weights=weights, k=1)[0]
    return foe_cls()


def _build_foes(node: MapNode, party: Party) -> list[FoeBase]:
    """Build a list of foes for the given room node.

    Ensures no duplicate foe IDs within a single encounter. If the available
    unique foe pool is smaller than the desired count, the final list is
    capped to the number of unique candidates.
    """
    if "boss" in node.room_type:
        foe = _choose_foe(party)
        foe.rank = "glitched boss" if "glitched" in node.room_type else "boss"
        return [foe]

    base = min(10, 1 + node.pressure // 5)
    extras = 0
    size = len(party.members)
    max_extra = max(size - 1, 0)
    if max_extra:
        if random.random() < 0.35:
            extras = max_extra
        else:
            for tier in range(max_extra - 1, 0, -1):
                if random.random() < 0.75:
                    extras = tier
                    break
    desired = min(10, base + extras)

    # Build a candidate pool of foe classes that are not members of the party
    party_ids = {p.id for p in party.members}
    candidates: list[type[FoeBase]] = []
    try:
        for name in getattr(foe_plugins, "__all__", []):
            cls = getattr(foe_plugins, name, None)
            if cls is None:
                continue
            try:
                if getattr(cls, "id", None) in party_ids:
                    continue
            except Exception:
                pass
            candidates.append(cls)
    except Exception:
        # Fallback: keep Slime as a candidate at minimum
        candidates = [foe_plugins.Slime]

    # Remove any accidental duplicates in the candidate list by ID
    unique_by_id: dict[str, type[FoeBase]] = {}
    for cls in candidates:
        try:
            cid = getattr(cls, "id", None)
            if cid and cid not in unique_by_id:
                unique_by_id[cid] = cls
        except Exception:
            # If a class has no static id, include it once under its name
            unique_by_id.setdefault(getattr(cls, "__name__", str(id(cls))), cls)

    pool = list(unique_by_id.values())
    if not pool:
        pool = [foe_plugins.Slime]
    weights = [
        3 if getattr(cls, "id", None) == "luna" and "luna" not in party_ids else 1
        for cls in pool
    ]

    k = min(desired, len(pool))
    chosen_classes: list[type[FoeBase]] = []
    candidates = pool[:]
    candidate_weights = weights[:]
    for _ in range(k):
        if not candidates:
            break
        cls = random.choices(candidates, weights=candidate_weights, k=1)[0]
        chosen_classes.append(cls)
        idx = candidates.index(cls)
        candidates.pop(idx)
        candidate_weights.pop(idx)
    foes = [cls() for cls in chosen_classes]
    for foe in foes:
        if "prime" in node.room_type:
            foe.rank = "glitched prime" if "glitched" in node.room_type else "prime"
        elif "glitched" in node.room_type:
            foe.rank = "glitched prime"
    return foes
