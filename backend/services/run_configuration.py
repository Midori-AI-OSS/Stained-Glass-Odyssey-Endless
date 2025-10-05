"""Run configuration metadata and validation helpers."""

from __future__ import annotations

from collections.abc import Mapping as ABCMapping
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
import hashlib
import json
from typing import Any
from typing import Mapping

from autofighter.effects import DIMINISHING_RETURNS_CONFIG
from autofighter.effects import calculate_diminishing_returns

METADATA_VERSION = "2025.02"

_PRESSURE_TOOLTIP = (
    "Each stack raises encounter pressure. Base encounters gain +1 foe slot for every "
    "five stacks (capped by the ten-slot spawn limit) before party-size bonuses. Foes roll "
    "a minimum defense floor of pressure × 10 that then varies between 0.82× and 1.50×. "
    "Prime and Glitched spawn odds each gain +1% per stack in addition to floor and room "
    "bonuses. Shop prices scale multiplicatively by 1.26^pressure with ±5% variance before "
    "repeat-visit taxes. Pressure does not add experience or rare drop bonuses; rewards "
    "are driven by party RDR, modifier bonuses, and per-foe payouts."
)


@dataclass(frozen=True)
class RunConfigurationSelection:
    """Validated configuration details for a run."""

    run_type: dict[str, Any]
    modifiers: dict[str, int]
    pressure: int
    reward_bonuses: dict[str, float]
    snapshot: dict[str, Any]

    def telemetry_payload(self) -> dict[str, Any]:
        """Return a sanitized payload for analytics logging."""

        return {
            "version": self.snapshot.get("version", METADATA_VERSION),
            "run_type": self.run_type.get("id"),
            "modifiers": self.modifiers,
            "reward_bonuses": {
                "exp_bonus": self.reward_bonuses.get("exp_bonus", 0.0),
                "rdr_bonus": self.reward_bonuses.get("rdr_bonus", 0.0),
                "foe_modifier_bonus": self.reward_bonuses.get("foe_modifier_bonus", 0.0),
                "player_modifier_bonus": self.reward_bonuses.get("player_modifier_bonus", 0.0),
            },
        }


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _pressure_effects(stacks: int) -> dict[str, Any]:
    extra_foes = stacks // 5
    defense_floor = stacks * 10
    elite_bonus = stacks
    shop_multiplier = 1.26 ** stacks if stacks else 1.0
    return {
        "stacks": stacks,
        "encounter_bonus": extra_foes,
        "defense_floor": defense_floor,
        "elite_spawn_bonus_pct": elite_bonus,
        "shop_multiplier": shop_multiplier,
        "tooltip": _PRESSURE_TOOLTIP,
    }


def _diminishing_factor(stat: str, stacks: int) -> float:
    if stacks <= 0:
        return 1.0
    config = DIMINISHING_RETURNS_CONFIG.get(stat)
    if not config:
        return 1.0
    threshold = float(config["threshold"])
    base_offset = float(config["base_offset"])
    current_value = base_offset + threshold * stacks
    try:
        return float(calculate_diminishing_returns(stat, current_value))
    except Exception:
        return 1.0


def _foe_modifier_effect(stat: str, per_stack: float, stacks: int) -> dict[str, Any]:
    raw_bonus = per_stack * stacks
    diminishing = _diminishing_factor(stat, stacks)
    effective_bonus = raw_bonus * diminishing
    return {
        "per_stack": per_stack,
        "stacks": stacks,
        "raw_bonus": raw_bonus,
        "diminishing_factor": diminishing,
        "effective_bonus": effective_bonus,
    }


def _percent_modifier_effect(per_stack: float, stacks: int) -> dict[str, Any]:
    raw_bonus = per_stack * stacks
    return {
        "per_stack": per_stack,
        "stacks": stacks,
        "raw_bonus": raw_bonus,
    }


def _character_stat_penalty(stacks: int) -> dict[str, Any]:
    capped = min(stacks, 500)
    overflow = max(stacks - 500, 0)
    penalty_primary = capped * 0.001
    penalty_overflow = overflow * 0.000001
    total_penalty = penalty_primary + penalty_overflow
    effective_multiplier = max(0.0, 1.0 - total_penalty)
    bonus_rdr = 0.0
    bonus_exp = 0.0
    if stacks > 0:
        bonus_rdr = 0.05 + max(0, stacks - 1) * 0.06
        bonus_exp = bonus_rdr
    return {
        "stacks": stacks,
        "penalty_primary": penalty_primary,
        "penalty_overflow": penalty_overflow,
        "total_penalty": total_penalty,
        "effective_multiplier": effective_multiplier,
        "bonus_rdr": bonus_rdr,
        "bonus_exp": bonus_exp,
    }


_MODIFIER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "pressure": {
        "id": "pressure",
        "label": "Pressure",
        "category": "core",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": False,
        "description": "Classic encounter scaler that increases foe count, defenses, elite odds, and shop taxes.",
        "effects_metadata": {
            "encounter_bonus": {
                "type": "step",
                "step_size": 5,
                "amount_per_step": 1,
                "maximum_additional_slots": 9,
                "description": "Adds +1 base foe slot for every five stacks before party-size adjustments.",
            },
            "defense_floor": {
                "type": "linear",
                "per_stack": 10,
                "variance_multiplier": [0.82, 1.5],
                "description": "Foes roll at least pressure × 10 defense before the 0.82×–1.50× variance band is applied.",
            },
            "elite_spawn_bonus_pct": {
                "type": "linear",
                "per_stack": 1,
                "description": "Prime and Glitched odds each gain +1 percentage point per stack.",
            },
            "shop_multiplier": {
                "type": "exponential",
                "base": 1.26,
                "description": "Shop prices multiply by 1.26^pressure (±5% variance before repeat-visit taxes).",
            },
        },
        "reward_bonuses": {
            "exp_bonus_per_stack": 0.0,
            "rdr_bonus_per_stack": 0.0,
        },
        "preview_stacks": [0, 1, 5, 10, 20],
        "effects": _pressure_effects,
    },
    "foe_speed": {
        "id": "foe_speed",
        "label": "Foe Speed",
        "category": "foe",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": True,
        "description": "Boosts foe action speed and initiative by +0.01× per stack before diminishing returns.",
        "effects_metadata": {
            "stat": "atk",
            "per_stack": 0.01,
            "scaling_type": "additive",
        },
        "diminishing_returns": {
            "applies": True,
            "stat": "atk",
            "source": "autofighter.effects.calculate_diminishing_returns",
        },
        "reward_bonuses": {
            "exp_bonus_per_stack": 0.5,
            "rdr_bonus_per_stack": 0.5,
        },
        "preview_stacks": [0, 1, 5, 10],
        "effects": lambda stacks: _percent_modifier_effect(0.01, stacks),
        "diminishing_stat": "atk",
    },
    "foe_hp": {
        "id": "foe_hp",
        "label": "Foe HP",
        "category": "foe",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": True,
        "description": "Raises foe max/current HP by +0.5× per stack before diminishing returns.",
        "effects_metadata": {
            "stat": "max_hp",
            "per_stack": 0.5,
            "scaling_type": "additive",
        },
        "diminishing_returns": {
            "applies": True,
            "stat": "max_hp",
            "source": "autofighter.effects.calculate_diminishing_returns",
        },
        "reward_bonuses": {
            "exp_bonus_per_stack": 0.5,
            "rdr_bonus_per_stack": 0.5,
        },
        "preview_stacks": [0, 1, 5, 10],
        "effects": lambda stacks: _foe_modifier_effect("max_hp", 0.5, stacks),
        "diminishing_stat": "max_hp",
    },
    "foe_mitigation": {
        "id": "foe_mitigation",
        "label": "Foe Mitigation",
        "category": "foe",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": True,
        "description": "Adds +0.00001 mitigation per stack with diminishing returns to curb runaway defenses.",
        "effects_metadata": {
            "stat": "mitigation",
            "per_stack": 0.00001,
            "scaling_type": "additive",
        },
        "diminishing_returns": {
            "applies": True,
            "stat": "mitigation",
            "source": "autofighter.effects.calculate_diminishing_returns",
        },
        "reward_bonuses": {
            "exp_bonus_per_stack": 0.5,
            "rdr_bonus_per_stack": 0.5,
        },
        "preview_stacks": [0, 1, 5, 10],
        "effects": lambda stacks: _foe_modifier_effect("mitigation", 0.00001, stacks),
        "diminishing_stat": "mitigation",
    },
    "foe_vitality": {
        "id": "foe_vitality",
        "label": "Foe Vitality",
        "category": "foe",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": True,
        "description": "Adds +0.00001 vitality per stack before diminishing returns for regeneration-heavy foes.",
        "effects_metadata": {
            "stat": "vitality",
            "per_stack": 0.00001,
            "scaling_type": "additive",
        },
        "diminishing_returns": {
            "applies": True,
            "stat": "vitality",
            "source": "autofighter.effects.calculate_diminishing_returns",
        },
        "reward_bonuses": {
            "exp_bonus_per_stack": 0.5,
            "rdr_bonus_per_stack": 0.5,
        },
        "preview_stacks": [0, 1, 5, 10],
        "effects": lambda stacks: _foe_modifier_effect("vitality", 0.00001, stacks),
        "diminishing_stat": "vitality",
    },
    "foe_glitched_rate": {
        "id": "foe_glitched_rate",
        "label": "Glitched Spawn Rate",
        "category": "foe",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": True,
        "description": "Increases Glitched foe spawn odds by +1% per stack.",
        "effects_metadata": {
            "stat": "glitched_chance",
            "per_stack": 0.01,
            "scaling_type": "additive",
        },
        "reward_bonuses": {
            "exp_bonus_per_stack": 0.5,
            "rdr_bonus_per_stack": 0.5,
        },
        "preview_stacks": [0, 1, 5, 10],
        "effects": lambda stacks: _percent_modifier_effect(0.01, stacks),
    },
    "foe_prime_rate": {
        "id": "foe_prime_rate",
        "label": "Prime Spawn Rate",
        "category": "foe",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": True,
        "description": "Increases Prime foe spawn odds by +1% per stack.",
        "effects_metadata": {
            "stat": "prime_chance",
            "per_stack": 0.01,
            "scaling_type": "additive",
        },
        "reward_bonuses": {
            "exp_bonus_per_stack": 0.5,
            "rdr_bonus_per_stack": 0.5,
        },
        "preview_stacks": [0, 1, 5, 10],
        "effects": lambda stacks: _percent_modifier_effect(0.01, stacks),
    },
    "character_stat_down": {
        "id": "character_stat_down",
        "label": "Character Stat Down",
        "category": "player",
        "min_stacks": 0,
        "stack_step": 1,
        "grants_reward_bonus": False,
        "description": (
            "Reduces all player stats by 0.001× per stack (0.000001× past 500 stacks) in exchange for"
            " escalating RDR/EXP bonuses."
        ),
        "effects_metadata": {
            "primary_penalty_per_stack": 0.001,
            "overflow_penalty_per_stack": 0.000001,
            "overflow_threshold": 500,
        },
        "reward_bonuses": {
            "exp_bonus_first_stack": 0.05,
            "exp_bonus_additional_stack": 0.06,
            "rdr_bonus_first_stack": 0.05,
            "rdr_bonus_additional_stack": 0.06,
        },
        "preview_stacks": [0, 1, 2, 10, 100, 500, 600],
        "effects": _character_stat_penalty,
    },
}


_RUN_TYPES: list[dict[str, Any]] = [
    {
        "id": "standard",
        "label": "Standard Expedition",
        "description": "Balanced adventure with classic pacing and full map variety.",
        "default_modifiers": {"pressure": 0},
        "allowed_modifiers": list(_MODIFIER_DEFINITIONS.keys()),
        "room_overrides": {},
    },
    {
        "id": "boss_rush",
        "label": "Boss Rush",
        "description": "Shortened gauntlet that escalates pressure quickly and leans on elite encounters.",
        "default_modifiers": {"pressure": 5, "foe_hp": 2, "foe_mitigation": 2},
        "allowed_modifiers": list(_MODIFIER_DEFINITIONS.keys()),
        "room_overrides": {"shop": 0, "rest": 0},
    },
]


def get_run_configuration_metadata() -> dict[str, Any]:
    """Return the canonical run type and modifier metadata."""

    modifiers: list[dict[str, Any]] = []
    for entry in _MODIFIER_DEFINITIONS.values():
        base = {
            "id": entry["id"],
            "label": entry["label"],
            "category": entry["category"],
            "min_stacks": entry["min_stacks"],
            "stack_step": entry["stack_step"],
            "grants_reward_bonus": entry["grants_reward_bonus"],
        }
        if "description" in entry:
            base["description"] = entry["description"]
        base["stacking"] = {
            "minimum": entry.get("min_stacks", 0),
            "step": entry.get("stack_step", 1),
            "maximum": entry.get("max_stacks"),
            "default": entry.get("default_stacks", entry.get("min_stacks", 0)),
        }
        base["reward_bonuses"] = entry.get("reward_bonuses", {})
        diminishing = entry.get("diminishing_returns")
        if not diminishing and entry.get("diminishing_stat"):
            diminishing = {
                "applies": True,
                "stat": entry["diminishing_stat"],
                "source": "autofighter.effects.calculate_diminishing_returns",
            }
        if diminishing:
            base["diminishing_returns"] = diminishing
        if "effects_metadata" in entry:
            base["effects"] = entry["effects_metadata"]
        if entry["id"] == "pressure":
            base["tooltip"] = _PRESSURE_TOOLTIP
        preview_stacks = entry.get("preview_stacks") or [0, 1, 5, 10]
        effects_fn = entry.get("effects")
        if callable(effects_fn):
            base["preview"] = [effects_fn(stacks) for stacks in preview_stacks]
        modifiers.append(base)

    return {
        "version": METADATA_VERSION,
        "generated_at": _now_iso(),
        "run_types": list(_RUN_TYPES),
        "modifiers": modifiers,
        "pressure": {
            "tooltip": _PRESSURE_TOOLTIP,
        },
    }


def _normalise_value(value: Any) -> int:
    if isinstance(value, Mapping) and "stacks" in value:
        value = value["stacks"]
    if isinstance(value, bool):
        raise ValueError("modifier stacks must be numeric")
    try:
        stacks = int(value)
    except (TypeError, ValueError):
        raise ValueError("modifier stacks must be numeric") from None
    if stacks < 0:
        raise ValueError("modifier stacks must be non-negative")
    return stacks


def validate_run_configuration(
    *,
    run_type: str | None,
    modifiers: Mapping[str, Any] | None,
    fallback_pressure: int | None = None,
) -> RunConfigurationSelection:
    """Validate requested run setup and compute reward adjustments."""

    metadata = get_run_configuration_metadata()
    run_type_id = (run_type or "standard").strip().lower() or "standard"
    run_type_entry = next((rt for rt in _RUN_TYPES if rt["id"] == run_type_id), None)
    if run_type_entry is None:
        raise ValueError("unknown run type")

    allowed = set(run_type_entry.get("allowed_modifiers", []))
    combined: dict[str, Any] = dict(run_type_entry.get("default_modifiers", {}))

    provided_pressure = False
    if modifiers is not None:
        if not isinstance(modifiers, Mapping):
            raise ValueError("modifiers must be an object")
        for key, value in modifiers.items():
            mod_id = str(key).strip().lower()
            combined[mod_id] = value
            if mod_id == "pressure":
                provided_pressure = True

    if fallback_pressure is not None and not provided_pressure:
        try:
            combined["pressure"] = int(fallback_pressure)
        except (TypeError, ValueError):
            raise ValueError("pressure must be numeric") from None

    normalized: dict[str, int] = {}
    modifier_snapshots: dict[str, Any] = {}
    foe_reward_stacks = 0
    player_bonus = 0.0
    char_penalty_snapshot: dict[str, Any] | None = None

    for key, value in combined.items():
        mod_id = str(key).strip().lower()
        definition = _MODIFIER_DEFINITIONS.get(mod_id)
        if definition is None:
            raise ValueError(f"unknown modifier: {mod_id}")
        if allowed and mod_id not in allowed:
            raise ValueError(f"modifier '{mod_id}' is not allowed for run type '{run_type_entry['id']}'")

        stacks = _normalise_value(value)
        if stacks < definition["min_stacks"]:
            raise ValueError(
                f"modifier '{mod_id}' requires at least {definition['min_stacks']} stack(s)"
            )

        normalized[mod_id] = stacks
        effects_fn = definition.get("effects")
        if callable(effects_fn):
            details = effects_fn(stacks)
        else:
            details = {"stacks": stacks}
        modifier_snapshots[mod_id] = {
            "id": mod_id,
            "label": definition.get("label", mod_id),
            "category": definition.get("category"),
            "details": details,
        }

        if definition.get("grants_reward_bonus"):
            foe_reward_stacks += stacks

        if mod_id == "character_stat_down":
            char_penalty_snapshot = details
            player_bonus = details.get("bonus_rdr", 0.0)

    pressure_value = int(normalized.get("pressure", 0))
    if char_penalty_snapshot is None:
        char_penalty_snapshot = _character_stat_penalty(0)
        modifier_snapshots.setdefault(
            "character_stat_down",
            {
                "id": "character_stat_down",
                "label": _MODIFIER_DEFINITIONS["character_stat_down"]["label"],
                "category": "player",
                "details": char_penalty_snapshot,
            },
        )

    reward_bonuses = {
        "foe_modifier_bonus": foe_reward_stacks * 0.5,
        "player_modifier_bonus": player_bonus,
    }
    reward_bonuses["exp_bonus"] = reward_bonuses["foe_modifier_bonus"] + reward_bonuses["player_modifier_bonus"]
    reward_bonuses["rdr_bonus"] = reward_bonuses["exp_bonus"]
    reward_bonuses["exp_multiplier"] = 1.0 + reward_bonuses["exp_bonus"]
    reward_bonuses["rdr_multiplier"] = 1.0 + reward_bonuses["rdr_bonus"]

    room_overrides = run_type_entry.get("room_overrides", {}) or {}

    snapshot = {
        "version": METADATA_VERSION,
        "generated_at": metadata["generated_at"],
        "run_type": {
            "id": run_type_entry["id"],
            "label": run_type_entry.get("label"),
            "description": run_type_entry.get("description"),
            "room_overrides": room_overrides,
        },
        "modifiers": modifier_snapshots,
        "pressure": _pressure_effects(pressure_value),
        "reward_bonuses": reward_bonuses,
        "room_overrides": room_overrides,
    }

    return RunConfigurationSelection(
        run_type={
            "id": run_type_entry["id"],
            "label": run_type_entry.get("label"),
            "room_overrides": room_overrides,
        },
        modifiers=normalized,
        pressure=pressure_value,
        reward_bonuses=reward_bonuses,
        snapshot=snapshot,
    )


@dataclass(frozen=True)
class RunModifierContext:
    """Derived modifier effects that downstream systems can reuse.

    The run startup wizard persists the raw configuration snapshot so gameplay
    systems do not need to replicate validation or metadata lookups.  This
    context condenses the snapshot into lightweight scalar values that map
    cleanly onto encounter generation, foe stat scaling, shop economy logic,
    and player stat adjustments.
    """

    pressure: int
    shop_multiplier: float
    shop_tax_multiplier: float
    shop_variance: tuple[float, float]
    elite_spawn_bonus_pct: float
    glitched_spawn_bonus_pct: float
    prime_spawn_bonus_pct: float
    foe_stat_multipliers: dict[str, float]
    foe_stat_deltas: dict[str, float]
    player_stat_multiplier: float
    pressure_defense_floor: float
    pressure_defense_min_roll: float
    pressure_defense_max_roll: float
    encounter_slot_bonus: int
    modifier_stacks: dict[str, int]
    metadata_hash: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the context into JSON-friendly primitives."""

        return {
            "pressure": self.pressure,
            "shop_multiplier": self.shop_multiplier,
            "shop_tax_multiplier": self.shop_tax_multiplier,
            "shop_variance": list(self.shop_variance),
            "elite_spawn_bonus_pct": self.elite_spawn_bonus_pct,
            "glitched_spawn_bonus_pct": self.glitched_spawn_bonus_pct,
            "prime_spawn_bonus_pct": self.prime_spawn_bonus_pct,
            "foe_stat_multipliers": dict(self.foe_stat_multipliers),
            "foe_stat_deltas": dict(self.foe_stat_deltas),
            "player_stat_multiplier": self.player_stat_multiplier,
            "pressure_defense_floor": self.pressure_defense_floor,
            "pressure_defense_min_roll": self.pressure_defense_min_roll,
            "pressure_defense_max_roll": self.pressure_defense_max_roll,
            "encounter_slot_bonus": self.encounter_slot_bonus,
            "modifier_stacks": dict(self.modifier_stacks),
            "metadata_hash": self.metadata_hash,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RunModifierContext":
        """Hydrate a context instance from serialized data."""

        mapping = dict(payload or {})

        def _pair(value: Any) -> tuple[float, float]:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                try:
                    return (float(value[0]), float(value[1]))
                except (TypeError, ValueError):
                    pass
            return (0.95, 1.05)

        return cls(
            pressure=int(mapping.get("pressure", 0)),
            shop_multiplier=float(mapping.get("shop_multiplier", 1.0) or 1.0),
            shop_tax_multiplier=float(mapping.get("shop_tax_multiplier", 1.0) or 1.0),
            shop_variance=_pair(mapping.get("shop_variance")),
            elite_spawn_bonus_pct=float(mapping.get("elite_spawn_bonus_pct", 0.0) or 0.0),
            glitched_spawn_bonus_pct=float(mapping.get("glitched_spawn_bonus_pct", 0.0) or 0.0),
            prime_spawn_bonus_pct=float(mapping.get("prime_spawn_bonus_pct", 0.0) or 0.0),
            foe_stat_multipliers=dict(mapping.get("foe_stat_multipliers", {})),
            foe_stat_deltas=dict(mapping.get("foe_stat_deltas", {})),
            player_stat_multiplier=float(mapping.get("player_stat_multiplier", 1.0) or 1.0),
            pressure_defense_floor=float(mapping.get("pressure_defense_floor", 0.0) or 0.0),
            pressure_defense_min_roll=float(mapping.get("pressure_defense_min_roll", 0.0) or 0.0),
            pressure_defense_max_roll=float(mapping.get("pressure_defense_max_roll", 0.0) or 0.0),
            encounter_slot_bonus=int(mapping.get("encounter_slot_bonus", 0) or 0),
            modifier_stacks=dict(mapping.get("modifier_stacks", {})),
            metadata_hash=str(mapping.get("metadata_hash", "")) or "",
        )


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, ABCMapping):
        return dict(value)
    return {}


def _modifier_entry(snapshot: Mapping[str, Any], modifier_id: str) -> dict[str, Any]:
    modifiers = _coerce_mapping(snapshot.get("modifiers"))
    return _coerce_mapping(modifiers.get(modifier_id, {}))


def get_modifier_details(snapshot: Mapping[str, Any], modifier_id: str) -> dict[str, Any]:
    """Return the stored detail block for ``modifier_id`` if present."""

    entry = _modifier_entry(snapshot, modifier_id)
    return _coerce_mapping(entry.get("details", {}))


def get_modifier_snapshot(snapshot: Mapping[str, Any], modifier_id: str) -> dict[str, Any]:
    """Return a normalized snapshot for ``modifier_id``.

    The configuration snapshot persisted on the run record mirrors the metadata
    exposed to the frontend wizard. Downstream systems frequently need to know
    both the stack count and any derived effect payloads without having to
    duplicate the normalisation logic that produced the snapshot.  This helper
    extracts the stored entry, coerces primitive fields into standard Python
    types, and falls back to sane defaults when the modifier is absent.
    """

    entry = _modifier_entry(snapshot, modifier_id)
    if not entry:
        return {"id": modifier_id, "stacks": 0, "details": {}}

    details = _coerce_mapping(entry.get("details", {}))

    raw_stacks = details.get("stacks") if details else entry.get("stacks")
    try:
        stacks = int(raw_stacks)
    except (TypeError, ValueError):
        stacks = 0

    summary = {
        "id": entry.get("id", modifier_id),
        "label": entry.get("label"),
        "category": entry.get("category"),
        "stacks": stacks,
        "details": details,
    }

    return summary


def _normalise_room_override(value: Any) -> dict[str, Any]:
    enabled = True
    count: int | None = None

    if isinstance(value, ABCMapping):
        if "enabled" in value:
            enabled = bool(value.get("enabled", True))
        numeric_candidate: Any | None = None
        for key in ("count", "quantity", "slots"):
            if key in value:
                numeric_candidate = value.get(key)
                break
        if numeric_candidate is not None:
            try:
                count = max(int(numeric_candidate), 0)
            except (TypeError, ValueError):
                count = 0
    elif isinstance(value, bool):
        enabled = value
    else:
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            numeric = None
        if numeric is None:
            enabled = bool(value)
        else:
            count = max(numeric, 0)

    if count is not None:
        if count <= 0:
            count = 0
            enabled = False
    return {"enabled": bool(enabled), "count": count}


def get_room_overrides(snapshot: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return normalised optional room directives embedded in the snapshot."""

    source = _coerce_mapping(snapshot)
    raw_overrides: Any = source.get("room_overrides")
    if not raw_overrides:
        run_type = _coerce_mapping(source.get("run_type"))
        raw_overrides = run_type.get("room_overrides")

    overrides: dict[str, dict[str, Any]] = {}
    if isinstance(raw_overrides, ABCMapping):
        for key, value in raw_overrides.items():
            if not key:
                continue
            room_type = str(key).strip()
            if not room_type:
                continue
            overrides[room_type] = _normalise_room_override(value)
    return overrides


def _numeric(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def build_run_modifier_context(snapshot: Mapping[str, Any]) -> RunModifierContext:
    """Extract reusable modifier effects from a configuration snapshot."""

    source = _coerce_mapping(snapshot)
    pressure_info = _coerce_mapping(source.get("pressure"))
    try:
        pressure_stacks = int(pressure_info.get("stacks", 0))
    except (TypeError, ValueError):
        pressure_stacks = 0

    shop_multiplier = _numeric(pressure_info.get("shop_multiplier"), default=1.0)
    elite_bonus_pct = _numeric(pressure_info.get("elite_spawn_bonus_pct"))

    modifiers = _coerce_mapping(source.get("modifiers"))
    modifier_stacks: dict[str, int] = {}

    def _stack_count(modifier_id: str) -> int:
        entry = _modifier_entry(source, modifier_id)
        details = _coerce_mapping(entry.get("details"))
        raw_value = details.get("stacks") if details else entry.get("stacks")
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return 0

    for modifier_id in modifiers:
        modifier_stacks[modifier_id] = _stack_count(modifier_id)

    def _effective_bonus(modifier_id: str) -> float:
        details = get_modifier_details(source, modifier_id)
        if "effective_bonus" in details:
            return _numeric(details.get("effective_bonus"))
        if "raw_bonus" in details:
            return _numeric(details.get("raw_bonus"))
        return 0.0

    foe_stat_multipliers: dict[str, float] = {}
    foe_stat_deltas: dict[str, float] = {}

    hp_bonus = _effective_bonus("foe_hp")
    if hp_bonus:
        foe_stat_multipliers["max_hp"] = 1.0 + hp_bonus

    speed_bonus = _effective_bonus("foe_speed")
    if speed_bonus:
        foe_stat_multipliers["spd"] = 1.0 + speed_bonus

    mitigation_bonus = _effective_bonus("foe_mitigation")
    if mitigation_bonus:
        foe_stat_deltas["mitigation"] = mitigation_bonus

    vitality_bonus = _effective_bonus("foe_vitality")
    if vitality_bonus:
        foe_stat_deltas["vitality"] = vitality_bonus

    glitched_bonus_pct = _numeric(
        _effective_bonus("foe_glitched_rate"),
    ) * 100.0
    prime_bonus_pct = _numeric(
        _effective_bonus("foe_prime_rate"),
    ) * 100.0

    char_penalty = get_modifier_details(source, "character_stat_down")
    player_stat_multiplier = _numeric(
        char_penalty.get("effective_multiplier"),
        default=1.0,
    )

    shop_tax_multiplier = 1.0
    shop_variance = (0.95, 1.05)

    def _update_variance(candidate: Any) -> tuple[float, float]:
        if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
            try:
                low, high = float(candidate[0]), float(candidate[1])
            except (TypeError, ValueError):
                return shop_variance
            if low <= high:
                return (low, high)
        return shop_variance

    for modifier_id, entry in modifiers.items():
        if modifier_id == "pressure":
            continue
        details = _coerce_mapping(entry.get("details"))
        if not details:
            continue
        multiplier = details.get("shop_multiplier")
        if multiplier is not None:
            shop_multiplier *= _numeric(multiplier, default=1.0)
        tax_multiplier = details.get("shop_tax_multiplier")
        if tax_multiplier is not None:
            shop_tax_multiplier *= _numeric(tax_multiplier, default=1.0)
        variance_candidate = details.get("shop_variance")
        if variance_candidate is not None:
            shop_variance = _update_variance(variance_candidate)

    pressure_defense_floor = _numeric(pressure_info.get("defense_floor"))
    pressure_defense_min_roll = _numeric(pressure_info.get("defense_min_roll"), default=0.82)
    pressure_defense_max_roll = _numeric(pressure_info.get("defense_max_roll"), default=1.50)
    encounter_bonus = int(pressure_info.get("encounter_bonus", 0) or 0)
    pressure_stacks = max(pressure_stacks, 0)
    if not shop_multiplier:
        shop_multiplier = 1.0
    base_variance = pressure_info.get("shop_variance")
    if base_variance is not None:
        shop_variance = _update_variance(base_variance)

    if pressure_stacks and not pressure_defense_floor:
        pressure_defense_floor = 10.0 * pressure_stacks

    if not shop_tax_multiplier:
        shop_tax_multiplier = 1.0

    # Include the snapshot version in the hash to keep context stable even when
    # future metadata fields are added.
    hash_material = json.dumps(
        {"version": source.get("version"), "modifiers": source.get("modifiers"), "pressure": pressure_info},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    metadata_hash = hashlib.sha256(hash_material).hexdigest()

    return RunModifierContext(
        pressure=pressure_stacks,
        shop_multiplier=shop_multiplier or 1.0,
        shop_tax_multiplier=shop_tax_multiplier or 1.0,
        shop_variance=shop_variance,
        elite_spawn_bonus_pct=elite_bonus_pct,
        glitched_spawn_bonus_pct=glitched_bonus_pct,
        prime_spawn_bonus_pct=prime_bonus_pct,
        foe_stat_multipliers=foe_stat_multipliers,
        foe_stat_deltas=foe_stat_deltas,
        player_stat_multiplier=player_stat_multiplier or 1.0,
        pressure_defense_floor=pressure_defense_floor,
        pressure_defense_min_roll=pressure_defense_min_roll,
        pressure_defense_max_roll=pressure_defense_max_roll,
        encounter_slot_bonus=encounter_bonus,
        modifier_stacks=modifier_stacks,
        metadata_hash=metadata_hash,
    )


__all__ = [
    "METADATA_VERSION",
    "RunConfigurationSelection",
    "RunModifierContext",
    "get_modifier_snapshot",
    "get_room_overrides",
    "build_run_modifier_context",
    "get_modifier_details",
    "get_run_configuration_metadata",
    "validate_run_configuration",
]

