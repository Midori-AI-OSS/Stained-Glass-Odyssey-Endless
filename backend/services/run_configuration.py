"""Run configuration metadata and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
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
    },
    {
        "id": "boss_rush",
        "label": "Boss Rush",
        "description": "Shortened gauntlet that escalates pressure quickly and leans on elite encounters.",
        "default_modifiers": {"pressure": 5, "foe_hp": 2, "foe_mitigation": 2},
        "allowed_modifiers": list(_MODIFIER_DEFINITIONS.keys()),
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

    snapshot = {
        "version": METADATA_VERSION,
        "generated_at": metadata["generated_at"],
        "run_type": {
            "id": run_type_entry["id"],
            "label": run_type_entry.get("label"),
            "description": run_type_entry.get("description"),
        },
        "modifiers": modifier_snapshots,
        "pressure": _pressure_effects(pressure_value),
        "reward_bonuses": reward_bonuses,
    }

    return RunConfigurationSelection(
        run_type={"id": run_type_entry["id"], "label": run_type_entry.get("label")},
        modifiers=normalized,
        pressure=pressure_value,
        reward_bonuses=reward_bonuses,
        snapshot=snapshot,
    )


__all__ = [
    "METADATA_VERSION",
    "RunConfigurationSelection",
    "get_run_configuration_metadata",
    "validate_run_configuration",
]

