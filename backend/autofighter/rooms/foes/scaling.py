from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
import random
from typing import Any

from autofighter.effects import StatModifier
from autofighter.effects import create_stat_buff
from autofighter.effects import get_current_stat_value
from autofighter.mapgen import MapGenerator
from autofighter.mapgen import MapNode
from autofighter.stats import Stats
from plugins.foes._base import FoeBase


def apply_permanent_scaling(
    stats: Stats,
    *,
    multipliers: Mapping[str, float] | None = None,
    deltas: Mapping[str, float] | None = None,
    name: str,
    modifier_id: str,
) -> StatModifier | None:
    """Apply a permanent stat modifier while respecting diminishing returns."""

    modifiers: dict[str, float] = {}
    if multipliers:
        for key, value in multipliers.items():
            if not isinstance(value, (int, float)):
                continue
            if not hasattr(stats, key):
                continue
            try:
                current_value = float(get_current_stat_value(stats, key))
            except Exception:
                continue
            multiplier = float(value)
            target_value = current_value * multiplier
            target_delta = 0.0
            base_adjusted = False
            base_value: float | None = None
            base_attr = f"_base_{key}"
            if (
                hasattr(stats, "get_base_stat")
                and hasattr(stats, "set_base_stat")
                and hasattr(stats, base_attr)
            ):
                try:
                    raw_base = stats.get_base_stat(key)
                except Exception:
                    raw_base = None
                if isinstance(raw_base, (int, float)):
                    base_value = float(raw_base)
                    existing_effect = current_value - base_value
                    new_base_value = target_value - existing_effect
                    try:
                        cast_value = type(raw_base)(new_base_value)
                    except Exception:
                        cast_value = new_base_value
                    try:
                        stats.set_base_stat(key, cast_value)
                        base_adjusted = True
                        current_value = float(get_current_stat_value(stats, key))
                    except Exception:
                        base_adjusted = False
            if base_adjusted:
                target_delta = target_value - current_value
            else:
                target_delta = target_value - current_value
            if abs(target_delta) < 1e-9:
                continue
            modifiers[key] = modifiers.get(key, 0.0) + target_delta
    if deltas:
        for key, value in deltas.items():
            if not isinstance(value, (int, float)):
                continue
            modifiers[key] = modifiers.get(key, 0.0) + float(value)
    if not modifiers:
        return None
    effect = create_stat_buff(
        stats,
        name=name,
        id=modifier_id,
        turns=-1,
        bypass_diminishing=False,
        **modifiers,
    )
    pending = getattr(stats, "_pending_mods", None)
    if pending is None:
        pending = []
        setattr(stats, "_pending_mods", pending)
    pending.append(effect)
    return effect


def calculate_cumulative_rooms(node: MapNode) -> int:
    """Return the cumulative room count for the provided node."""

    try:
        floor_index = max(int(node.floor) - 1, 0)
    except Exception:
        floor_index = 0
    try:
        local_index = max(int(node.index), 0)
    except Exception:
        local_index = 0
    return floor_index * MapGenerator.rooms_per_floor + local_index


def compute_base_multiplier(
    strength: float,
    node: MapNode,
    config: Mapping[str, Any],
    *,
    cumulative_rooms: int | None = None,
    rng: random.Random | None = None,
) -> float:
    """Calculate the primary stat multiplier for foe scaling."""

    random_source = rng or random
    variance = float(config.get("scaling_variance", 0.0))
    starter_int = 1.0 + random_source.uniform(-variance, variance)

    if cumulative_rooms is None:
        cumulative_rooms = calculate_cumulative_rooms(node)
    room_growth = float(config.get("room_growth_multiplier", 0.0))
    try:
        room_term = max(cumulative_rooms - 1, 0)
    except Exception:
        room_term = 0
    room_mult = starter_int + room_growth * room_term

    loop_growth = float(config.get("loop_growth_multiplier", 0.0))
    try:
        loop_term = max(int(getattr(node, "loop", 1)) - 1, 0)
    except Exception:
        loop_term = 0
    loop_mult = starter_int + loop_growth * loop_term

    pressure_multiplier = float(config.get("pressure_multiplier", 1.0))
    try:
        pressure_term = max(int(getattr(node, "pressure", 0)), 1)
    except Exception:
        pressure_term = 1
    pressure_mult = pressure_multiplier * pressure_term

    try:
        base_mult = float(strength) * room_mult * loop_mult * pressure_mult
    except Exception:
        base_mult = room_mult * loop_mult * pressure_mult
    return max(base_mult, 0.5)


def apply_base_debuffs(
    stats: Stats,
    node: MapNode,
    config: Mapping[str, Any],
) -> float:
    """Apply the baseline foe debuffs and return the applied multiplier."""

    foe_debuff = 1.0
    if isinstance(stats, FoeBase):
        foe_debuff = float(config.get("foe_base_debuff", 1.0))
        apply_permanent_scaling(
            stats,
            multipliers={"atk": foe_debuff, "max_hp": foe_debuff},
            name="Base foe debuff",
            modifier_id=str(config.get("base_debuff_id", "foe_base_debuff")),
        )
        defense_multiplier = min((foe_debuff * getattr(node, "floor", 0)) / 4, 1.0)
        apply_permanent_scaling(
            stats,
            multipliers={"defense": defense_multiplier},
            name="Base foe defense debuff",
            modifier_id=f"{config.get('base_debuff_id', 'foe_base_debuff')}_defense",
        )
    else:
        apply_permanent_scaling(
            stats,
            multipliers={"atk": 1.0, "max_hp": 1.0},
            name="Base foe debuff",
            modifier_id=str(config.get("base_debuff_id", "foe_base_debuff")),
        )
    return foe_debuff


def apply_attribute_scaling(
    stats: Stats,
    base_multiplier: float,
    config: Mapping[str, Any],
    *,
    rng: random.Random | None = None,
) -> None:
    """Scale numeric stats using the provided multiplier."""

    random_source = rng or random
    variance = float(config.get("scaling_variance", 0.0))
    base_stat_aliases = {
        "max_hp",
        "atk",
        "defense",
        "crit_rate",
        "crit_damage",
        "effect_hit_rate",
        "mitigation",
        "regain",
        "dodge_odds",
        "effect_resistance",
        "vitality",
    }
    multipliers: dict[str, float] = {}
    for field_info in fields(type(stats)):
        name = field_info.name
        if name in {"exp", "level", "exp_multiplier"} or name.startswith("_"):
            continue
        target_name = name
        if target_name.startswith("base_"):
            alias = target_name[5:]
            if alias in base_stat_aliases:
                target_name = alias
            else:
                continue
        value = getattr(stats, target_name, None)
        if isinstance(value, (int, float)):
            per_stat_variation = 1.0 + random_source.uniform(-variance, variance)
            multipliers[target_name] = base_multiplier * per_stat_variation
    apply_permanent_scaling(
        stats,
        multipliers=multipliers,
        name="Room scaling",
        modifier_id=str(config.get("scaling_modifier_id", "foe_room_scaling")),
    )


def enforce_thresholds(
    stats: Stats,
    node: MapNode,
    config: Mapping[str, Any],
    *,
    cumulative_rooms: int,
    foe_debuff: float,
    rng: random.Random | None = None,
) -> None:
    """Clamp stats after scaling to maintain gameplay constraints."""

    random_source = rng or random

    try:
        room_num = max(int(cumulative_rooms), 1)
        desired = max(1, int(room_num / 2))
        stats.level = int(max(getattr(stats, "level", 1), desired))
    except Exception:
        pass

    try:
        room_num = max(int(getattr(node, "index", 0)), 1)
        base_hp = int(15 * room_num * (foe_debuff if isinstance(stats, FoeBase) else 1.0))
        low = int(base_hp * 0.85)
        high = int(base_hp * 1.10)
        target = random_source.randint(low, max(high, low + 1))
        current_max = int(getattr(stats, "max_hp", 1))
        new_max = max(current_max, target)
        stats.set_base_stat("max_hp", new_max)
        stats.hp = new_max
    except Exception:
        pass

    try:
        cd = getattr(stats, "crit_damage", None)
        if isinstance(cd, (int, float)):
            stats.set_base_stat("crit_damage", max(float(cd), 2.0))
    except Exception:
        pass

    if isinstance(stats, FoeBase):
        try:
            er = getattr(stats, "effect_resistance", None)
            if isinstance(er, (int, float)):
                stats.set_base_stat("effect_resistance", max(0.0, float(er)))
        except Exception:
            pass
        try:
            apt = getattr(stats, "actions_per_turn", None)
            if isinstance(apt, (int, float)):
                stats.actions_per_turn = int(
                    min(
                        max(1, int(apt)),
                        int(config.get("max_actions_per_turn", 1)),
                    )
                )
        except Exception:
            pass
        try:
            ap = getattr(stats, "action_points", None)
            if isinstance(ap, (int, float)):
                stats.action_points = int(
                    min(
                        max(0, int(ap)),
                        int(config.get("max_action_points", 1)),
                    )
                )
        except Exception:
            pass

    try:
        if isinstance(stats, FoeBase):
            current = getattr(stats, "defense", None)
            if isinstance(current, (int, float)):
                override = getattr(stats, "min_defense_override", None)
                if isinstance(override, (int, float)):
                    min_def = max(int(override), 0)
                else:
                    min_def = 2 + cumulative_rooms
                if current < min_def:
                    stats.set_base_stat("defense", min_def)
    except Exception:
        pass

    try:
        if isinstance(stats, FoeBase) and getattr(node, "pressure", 0) > 0:
            current = getattr(stats, "defense", None)
            if isinstance(current, (int, float)):
                base_def = getattr(node, "pressure", 0) * float(
                    config.get("pressure_defense_floor", 0)
                )
                min_factor = float(config.get("pressure_defense_min_roll", 0.0))
                max_factor = float(config.get("pressure_defense_max_roll", 0.0))
                random_factor = random_source.uniform(min_factor, max_factor)
                pressure_defense = int(base_def * random_factor)
                if pressure_defense > current:
                    stats.set_base_stat("defense", pressure_defense)
    except Exception:
        pass

    for attr, threshold, step, base in (
        ("vitality", 0.5, 0.25, 5.0),
        ("mitigation", 0.2, 0.01, 5.0),
    ):
        try:
            if isinstance(stats, FoeBase):
                value = getattr(stats, attr, None)
                if isinstance(value, (int, float)):
                    fval = float(value)
                    if fval < threshold:
                        fval = threshold
                    else:
                        excess = fval - threshold
                        steps = int(excess // step)
                        factor = base + steps
                        fval = threshold + (excess / factor)
                        fval = max(fval, threshold)
                    stats.set_base_stat(attr, fval)
        except Exception:
            pass
