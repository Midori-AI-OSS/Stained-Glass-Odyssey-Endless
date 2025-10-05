"""Helper utilities for selecting foe spawn templates."""

from __future__ import annotations

from collections.abc import Collection
from collections.abc import Mapping
import random
from typing import Any

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.foes import SpawnTemplate
from services.run_configuration import RunModifierContext


def _weight_for_template(
    template: SpawnTemplate,
    *,
    node: MapNode,
    party_ids: Collection[str],
    recent_ids: Collection[str] | None,
    boss: bool,
) -> float:
    """Return a selection weight for the given template."""

    hook = template.weight_hook
    if not callable(hook):
        return 1.0
    try:
        weight = hook(
            node=node,
            party_ids=party_ids,
            recent_ids=recent_ids,
            boss=boss,
        )
    except Exception:
        return 1.0
    try:
        return float(weight)
    except Exception:
        return 1.0


def _adjust_recent_weight(
    weight: float,
    template_id: str,
    recent_ids: Collection[str] | None,
    config: Mapping[str, Any] | None,
) -> float:
    if not recent_ids or template_id not in recent_ids:
        return weight

    factor = 1.0
    minimum = 0.0
    if config is not None:
        try:
            factor = float(config.get("recent_weight_factor", 1.0))
        except Exception:
            factor = 1.0
        try:
            minimum = float(config.get("recent_weight_min", 0.0))
        except Exception:
            minimum = 0.0
    adjusted = weight * factor
    if adjusted <= 0.0:
        return max(minimum, 0.0)
    return max(adjusted, minimum)


def _sample_templates(
    count: int,
    *,
    templates: Mapping[str, SpawnTemplate],
    node: MapNode,
    party_ids: Collection[str],
    recent_ids: Collection[str] | None = None,
    config: Mapping[str, Any] | None = None,
    rng: random.Random | None = None,
) -> list[SpawnTemplate]:
    """Sample encounter templates while respecting recent foe history."""

    rng = rng or random
    pool: list[SpawnTemplate] = [
        template for template in templates.values() if template.id not in party_ids
    ]
    if not pool:
        return []

    unique: dict[str, SpawnTemplate] = {}
    for template in pool:
        unique.setdefault(template.id, template)
    candidates = list(unique.values())

    weights: list[float] = []
    for template in candidates:
        weight = _weight_for_template(
            template,
            node=node,
            party_ids=party_ids,
            recent_ids=recent_ids,
            boss=False,
        )
        if weight > 0.0:
            weight = _adjust_recent_weight(weight, template.id, recent_ids, config)
        weights.append(max(weight, 0.0))

    selected: list[SpawnTemplate] = []
    candidate_weights = weights[:]
    limit = min(count, len(candidates))
    for _ in range(limit):
        if not candidates:
            break
        if not any(weight > 0.0 for weight in candidate_weights):
            candidate_weights = [1.0 for _ in candidates]
        choice = rng.choices(candidates, weights=candidate_weights, k=1)[0]
        selected.append(choice)
        idx = candidates.index(choice)
        candidates.pop(idx)
        candidate_weights.pop(idx)
    return selected


def _choose_template(
    *,
    templates: Mapping[str, SpawnTemplate],
    node: MapNode,
    party_ids: Collection[str],
    recent_ids: Collection[str] | None,
    boss: bool,
    rng: random.Random | None = None,
) -> SpawnTemplate | None:
    """Choose a single template for encounters such as boss rooms."""

    rng = rng or random
    candidates = [
        template for template in templates.values() if template.id not in party_ids
    ]
    if not candidates:
        return None

    weights = [
        max(
            _weight_for_template(
                template,
                node=node,
                party_ids=party_ids,
                recent_ids=recent_ids,
                boss=boss,
            ),
            0.0,
        )
        for template in candidates
    ]
    if not any(weight > 0.0 for weight in weights):
        weights = [1.0 for _ in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]


def _desired_count(
    node: MapNode,
    party: Party,
    *,
    config: Mapping[str, Any],
    context: RunModifierContext | None = None,
    rng: random.Random | None = None,
) -> int:
    """Calculate the number of foes to spawn for the encounter."""

    rng = rng or random

    try:
        base_cap = int(config.get("base_spawn_cap", 1))
    except Exception:
        base_cap = 1
    try:
        pressure_base = int(config.get("pressure_spawn_base", 0))
    except Exception:
        pressure_base = 0
    try:
        pressure_step = int(config.get("pressure_spawn_step", 1))
    except Exception:
        pressure_step = 1

    if context is not None:
        try:
            pressure = max(int(context.pressure), 0)
        except Exception:
            pressure = 0
        encounter_bonus = max(int(getattr(context, "encounter_slot_bonus", 0)), 0)
    else:
        try:
            pressure = int(getattr(node, "pressure", 0))
        except Exception:
            pressure = 0
        encounter_bonus = 0

    effective_step = pressure_step if pressure_step > 0 else 1
    base = min(base_cap, pressure_base + max(pressure, 0) // effective_step)
    base = min(base_cap, base + encounter_bonus)

    extras = 0
    members_obj = getattr(party, "members", [])
    if isinstance(members_obj, Collection):
        size = len(members_obj)
    else:
        try:
            materialized = list(members_obj)
        except Exception:
            materialized = []
        size = len(materialized)
    max_extra = max(size - 1, 0)
    if max_extra:
        try:
            full_chance = float(config.get("party_extra_full_chance", 0.0))
        except Exception:
            full_chance = 0.0
        try:
            step_chance = float(config.get("party_extra_step_chance", 0.0))
        except Exception:
            step_chance = 0.0
        if rng.random() < full_chance:
            extras = max_extra
        else:
            for tier in range(max_extra - 1, 0, -1):
                if rng.random() < step_chance:
                    extras = tier
                    break
    return min(base_cap, base + extras)


__all__ = [
    "_weight_for_template",
    "_sample_templates",
    "_choose_template",
    "_desired_count",
]
