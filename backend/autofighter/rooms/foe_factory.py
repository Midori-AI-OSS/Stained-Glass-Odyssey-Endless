from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any
from typing import Collection
from typing import Mapping

from services.run_configuration import RunModifierContext

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.foes import SpawnTemplate
from autofighter.rooms.foes.catalog import load_catalog
from autofighter.rooms.foes.scaling import apply_attribute_scaling
from autofighter.rooms.foes.scaling import apply_base_debuffs
from autofighter.rooms.foes.scaling import apply_permanent_scaling
from autofighter.rooms.foes.scaling import calculate_cumulative_rooms
from autofighter.rooms.foes.scaling import compute_base_multiplier
from autofighter.rooms.foes.scaling import enforce_thresholds
from autofighter.rooms.foes.selector import _choose_template
from autofighter.rooms.foes.selector import _desired_count
from autofighter.rooms.foes.selector import _sample_templates
from autofighter.rooms.foes.selector import _weight_for_template
from autofighter.stats import Stats
from plugins.characters.foe_base import FoeBase


@dataclass
class SpawnResult:
    """Concrete foe instance produced by the factory."""

    foe: FoeBase


ROOM_BALANCE_CONFIG: dict[str, Any] = {
    "foe_base_debuff": 0.5,
    "room_growth_multiplier": 0.85,
    "loop_growth_multiplier": 1.30,
    "pressure_multiplier": 1.0,
    "scaling_variance": 0.05,
    "pressure_defense_floor": 10,
    "pressure_defense_min_roll": 0.82,
    "pressure_defense_max_roll": 1.50,
    "recent_weight_factor": 0.25,
    "recent_weight_min": 0.1,
    "max_actions_per_turn": 1,
    "max_action_points": 1,
    "party_extra_full_chance": 0.35,
    "party_extra_step_chance": 0.75,
    "base_spawn_cap": 10,
    "pressure_spawn_base": 1,
    "pressure_spawn_step": 5,
    "base_debuff_id": "foe_base_debuff",
    "scaling_modifier_id": "foe_room_scaling",
    "pressure_modifier_id": "foe_pressure_scaling",
}
class FoeFactory:
    """Factory responsible for foe discovery and encounter assembly."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(ROOM_BALANCE_CONFIG)
        if config:
            self.config.update(config)
        (
            self._templates,
            self._player_templates,
            self._adjectives,
        ) = load_catalog()
        self._weight_for_template = _weight_for_template

    @property
    def templates(self) -> Mapping[str, SpawnTemplate]:
        return self._templates

    def _choose_adjective(self) -> type | None:
        if not self._adjectives:
            return None
        return random.choice(self._adjectives)

    def _instantiate(self, template: SpawnTemplate) -> SpawnResult:
        foe = template.cls()
        foe.rank = template.base_rank
        if template.apply_adjective:
            adj_cls = self._choose_adjective()
            if adj_cls is not None:
                try:
                    adjective = adj_cls()
                    original_name = getattr(foe, "name", foe.id)
                    adjective.apply(foe)
                    foe.name = f"{adjective.name} {original_name}".strip()
                except Exception:
                    pass
        return SpawnResult(foe=foe)

    def build_encounter(
        self,
        node: MapNode,
        party: Party,
        *,
        exclude_ids: Collection[str] | None = None,
        recent_ids: Collection[str] | None = None,
        progression: Mapping[str, Any] | None = None,
    ) -> list[FoeBase]:
        progression_info: Mapping[str, Any] = progression or {}
        total_rooms = progression_info.get("total_rooms_cleared", 0)
        floors = progression_info.get("floors_cleared", 0)
        context: RunModifierContext | None = getattr(party, "run_modifier_context", None)
        config = dict(self.config)
        pressure_override = progression_info.get("current_pressure")
        if context is not None:
            try:
                pressure_override = int(getattr(context, "pressure", pressure_override))
            except Exception:
                pressure_override = getattr(node, "pressure", 0)
            try:
                per_stack_floor = context.pressure_defense_floor / max(context.pressure, 1) if context.pressure else config.get("pressure_defense_floor", 10)
                config["pressure_defense_floor"] = per_stack_floor
            except Exception:
                pass
            try:
                config["pressure_defense_min_roll"] = float(context.pressure_defense_min_roll)
            except Exception:
                pass
            try:
                config["pressure_defense_max_roll"] = float(context.pressure_defense_max_roll)
            except Exception:
                pass
            config["pressure_spawn_base"] = max(int(config.get("pressure_spawn_base", 1)), 1)
            speed_multiplier = context.foe_stat_multipliers.get("spd") if context.foe_stat_multipliers else None
            if speed_multiplier:
                try:
                    base_actions = int(config.get("max_actions_per_turn", 1))
                    config["max_actions_per_turn"] = max(1, min(5, round(base_actions * speed_multiplier)))
                except Exception:
                    pass
            try:
                config["pressure_multiplier"] = max(float(context.foe_strength_score), 1.0)
            except Exception:
                pass
        elif pressure_override is None:
            pressure_override = getattr(node, "pressure", 0)
        prime_chance, glitched_chance = self.calculate_rank_probabilities(
            total_rooms,
            floors,
            pressure_override,
            context=context,
        )
        room_type = getattr(node, "room_type", "") or ""
        forced_prime = "prime" in room_type
        forced_glitched = "glitched" in room_type
        party_ids = {p.id for p in party.members}
        if exclude_ids:
            party_ids.update(str(eid) for eid in exclude_ids if eid)
        recent_set = {str(rid) for rid in (recent_ids or []) if rid}

        if "boss" in room_type:
            template = _choose_template(
                templates=self._templates,
                node=node,
                party_ids=party_ids,
                recent_ids=recent_set,
                boss=True,
            )
            if template is None:
                template = self._templates.get("slime") or next(iter(self._templates.values()))
            foe = self._instantiate(template).foe
            is_prime = forced_prime or (prime_chance > 0 and random.random() < prime_chance)
            is_glitched = forced_glitched or (glitched_chance > 0 and random.random() < glitched_chance)
            if is_prime and is_glitched:
                foe.rank = "glitched prime boss"
            elif is_prime:
                foe.rank = "prime boss"
            elif is_glitched:
                foe.rank = "glitched boss"
            else:
                foe.rank = "boss"
            if context is not None:
                apply_permanent_scaling(
                    foe,
                    multipliers=context.foe_stat_multipliers,
                    deltas=context.foe_stat_deltas,
                    name="Run modifier scaling",
                    modifier_id=f"{config.get('scaling_modifier_id', 'foe_room_scaling')}_run_mod",
                )
                try:
                    foe.hp = foe.max_hp
                except Exception:
                    pass
            return [foe]

        desired = _desired_count(
            node,
            party,
            config=config,
            context=context,
        )
        templates = _sample_templates(
            desired,
            templates=self._templates,
            node=node,
            party_ids=party_ids,
            recent_ids=recent_set,
            config=config,
        )
        foes: list[FoeBase] = []
        for template in templates:
            spawn = self._instantiate(template)
            foe = spawn.foe
            is_prime = forced_prime or (prime_chance > 0 and random.random() < prime_chance)
            is_glitched = forced_glitched or (glitched_chance > 0 and random.random() < glitched_chance)
            if is_prime and is_glitched:
                foe.rank = "glitched prime"
            elif is_prime:
                foe.rank = "prime"
            elif is_glitched:
                foe.rank = "glitched"
            if context is not None:
                apply_permanent_scaling(
                    foe,
                    multipliers=context.foe_stat_multipliers,
                    deltas=context.foe_stat_deltas,
                    name="Run modifier scaling",
                    modifier_id=f"{config.get('scaling_modifier_id', 'foe_room_scaling')}_run_mod",
                )
                try:
                    foe.hp = foe.max_hp
                except Exception:
                    pass
            foes.append(foe)
        return foes

    @staticmethod
    def calculate_rank_probabilities(
        total_rooms_cleared: int = 0,
        floors_cleared: int = 0,
        pressure: int = 0,
        *,
        context: RunModifierContext | None = None,
    ) -> tuple[float, float]:
        try:
            rooms = max(int(total_rooms_cleared), 0)
        except Exception:
            rooms = 0
        try:
            floors = max(int(floors_cleared), 0)
        except Exception:
            floors = 0
        try:
            pressure_value = max(int(pressure), 0)
        except Exception:
            pressure_value = 0

        base_rate = rooms * 0.000001
        if floors > 0:
            try:
                floor_multiplier = max(1.0, pow(2.0, floors))
            except OverflowError:
                floor_multiplier = float("inf")
        else:
            floor_multiplier = 1.0
        scaled_rate = base_rate * floor_multiplier
        if context is None:
            pressure_bonus = pressure_value * 0.01
            glitched_bonus = 0.0
            prime_bonus = 0.0
        else:
            pressure_bonus = max(context.elite_spawn_bonus_pct, 0.0) / 100.0
            glitched_bonus = max(context.glitched_spawn_bonus_pct, 0.0) / 100.0
            prime_bonus = max(context.prime_spawn_bonus_pct, 0.0) / 100.0
        base_total = max(scaled_rate + pressure_bonus, 0.0)
        glitched_rate = min(1.0, max(base_total + glitched_bonus, 0.0))
        prime_rate = min(1.0, max(base_total + prime_bonus, 0.0))
        return prime_rate, glitched_rate

    def scale_stats(
        self, obj: Stats, node: MapNode, strength: float = 1.0, context: RunModifierContext | None = None
    ) -> None:
        if context is None:
            context = getattr(node, "run_modifier_context", None)

        cumulative_rooms = calculate_cumulative_rooms(node)
        baseline_stats: dict[str, float] = {}
        for key in ("max_hp", "atk", "defense"):
            try:
                value = getattr(obj, key)
            except Exception:
                value = None
            if isinstance(value, (int, float)):
                baseline_stats[key] = float(value)
        config = dict(self.config)
        if context is not None:
            try:
                per_stack_floor = context.pressure_defense_floor / max(context.pressure, 1) if context.pressure else config.get("pressure_defense_floor", 10)
                config["pressure_defense_floor"] = per_stack_floor
            except Exception:
                pass
            pressure_defense_min_roll = getattr(context, "pressure_defense_min_roll", None)
            if pressure_defense_min_roll is not None:
                config["pressure_defense_min_roll"] = pressure_defense_min_roll
            pressure_defense_max_roll = getattr(context, "pressure_defense_max_roll", None)
            if pressure_defense_max_roll is not None:
                config["pressure_defense_max_roll"] = pressure_defense_max_roll
        base_mult = compute_base_multiplier(
            strength,
            node,
            config,
            cumulative_rooms=cumulative_rooms,
        )
        foe_debuff = apply_base_debuffs(obj, node, config)
        if foe_debuff < 1.0 and isinstance(obj, FoeBase):
            for stat_name in list(baseline_stats.keys()):
                updated_baseline: float | None = None
                if hasattr(obj, "get_base_stat"):
                    try:
                        value = obj.get_base_stat(stat_name)
                    except Exception:
                        value = None
                    if isinstance(value, (int, float)):
                        updated_baseline = float(value)
                if updated_baseline is None:
                    try:
                        value = getattr(obj, stat_name)
                    except Exception:
                        value = None
                    if isinstance(value, (int, float)):
                        updated_baseline = float(value)
                if updated_baseline is not None:
                    baseline_stats[stat_name] = updated_baseline
                else:
                    baseline_stats.pop(stat_name, None)
        apply_attribute_scaling(
            obj,
            base_mult,
            config,
        )
        enforce_thresholds(
            obj,
            node,
            config,
            cumulative_rooms=cumulative_rooms,
            foe_debuff=foe_debuff,
        )
        for stat_name, baseline in baseline_stats.items():
            try:
                current = getattr(obj, stat_name)
            except Exception:
                continue
            if isinstance(current, (int, float)) and current < baseline:
                try:
                    obj.set_base_stat(stat_name, baseline)
                except Exception:
                    continue
        if context is not None:
            apply_permanent_scaling(
                obj,
                multipliers=context.foe_stat_multipliers,
                deltas=context.foe_stat_deltas,
                name="Run modifier scaling",
                modifier_id=f"{config.get('scaling_modifier_id', 'foe_room_scaling')}_run_mod",
            )
            try:
                obj.hp = obj.max_hp
            except Exception:
                pass


_FACTORY: FoeFactory | None = None


def get_foe_factory() -> FoeFactory:
    global _FACTORY
    if _FACTORY is None:
        _FACTORY = FoeFactory()
    return _FACTORY

