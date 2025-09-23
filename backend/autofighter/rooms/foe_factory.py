from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from pathlib import Path
import random
from typing import Any
from typing import Callable
from typing import Collection
from typing import Iterable
from typing import Mapping

from autofighter.effects import StatModifier
from autofighter.effects import create_stat_buff
from autofighter.effects import get_current_stat_value
from autofighter.mapgen import MapGenerator
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.stats import Stats
from plugins.foes._base import FoeBase
from plugins.plugin_loader import PluginLoader


@dataclass(frozen=True)
class SpawnTemplate:
    """Metadata describing a foe spawn template."""

    id: str
    cls: type[FoeBase]
    tags: frozenset[str] = field(default_factory=frozenset)
    weight_hook: Callable[[MapNode, Collection[str], Collection[str] | None, bool], float] | None = None
    base_rank: str = "normal"
    apply_adjective: bool = False


@dataclass
class SpawnResult:
    """Concrete foe instance produced by the factory."""

    foe: FoeBase
    modifiers: list[StatModifier]


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


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[2] / "plugins"


def _ensure_pending(stats: Stats, modifier: StatModifier) -> None:
    pending = getattr(stats, "_pending_mods", None)
    if pending is None:
        pending = []
        setattr(stats, "_pending_mods", pending)
    pending.append(modifier)


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
    _ensure_pending(stats, effect)
    return effect


class FoeFactory:
    """Factory responsible for foe discovery and encounter assembly."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(ROOM_BALANCE_CONFIG)
        if config:
            self.config.update(config)
        loader = PluginLoader()
        root = _plugin_root()
        for category in ("foes", "players", "themedadj"):
            loader.discover(str(root / category))
        try:
            foes = loader.get_plugins("foe")
        except Exception:
            foes = {}
        try:
            players = loader.get_plugins("player")
        except Exception:
            players = {}
        try:
            adjectives = loader.get_plugins("themedadj")
        except Exception:
            adjectives = {}
        self._adjectives: list[type] = list(adjectives.values())
        self._templates: dict[str, SpawnTemplate] = {}
        for foe_cls in foes.values():
            ident = getattr(foe_cls, "id", foe_cls.__name__)
            tags = frozenset(getattr(foe_cls, "spawn_tags", ()) or ())
            hook = getattr(foe_cls, "get_spawn_weight", None)
            self._templates[ident] = SpawnTemplate(
                id=ident,
                cls=foe_cls,
                tags=tags,
                weight_hook=hook,
                base_rank=getattr(foe_cls, "rank", "normal"),
            )
        self._player_templates: dict[str, SpawnTemplate] = {}
        for player_cls in players.values():
            ident = getattr(player_cls, "id", player_cls.__name__)
            if ident in self._templates:
                continue
            wrapper = self._wrap_player(player_cls)
            hook = getattr(player_cls, "get_spawn_weight", None)
            template = SpawnTemplate(
                id=ident,
                cls=wrapper,
                tags=frozenset({"player_template"}),
                weight_hook=hook,
                base_rank=getattr(wrapper, "rank", "normal"),
                apply_adjective=True,
            )
            self._templates[ident] = template
            self._player_templates[ident] = template

    def _wrap_player(self, cls: type) -> type[FoeBase]:
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

    @property
    def templates(self) -> Mapping[str, SpawnTemplate]:
        return self._templates

    def _weight_for_template(
        self,
        template: SpawnTemplate,
        *,
        node: MapNode,
        party_ids: Collection[str],
        recent_ids: Collection[str] | None,
        boss: bool,
    ) -> float:
        hook = template.weight_hook
        if not callable(hook):
            return 1.0
        try:
            return float(
                hook(
                    node=node,
                    party_ids=party_ids,
                    recent_ids=recent_ids,
                    boss=boss,
                )
            )
        except Exception:
            return 1.0

    def _choose_adjective(self) -> type | None:
        if not self._adjectives:
            return None
        return random.choice(self._adjectives)

    def _instantiate(self, template: SpawnTemplate) -> SpawnResult:
        foe = template.cls()
        modifiers: list[StatModifier] = []
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
        pending: Iterable[StatModifier] = getattr(foe, "_pending_mods", [])
        modifiers.extend(pending)
        return SpawnResult(foe=foe, modifiers=modifiers)

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
        pressure_override = progression_info.get("current_pressure")
        if pressure_override is None:
            pressure_override = getattr(node, "pressure", 0)
        prime_chance, glitched_chance = self.calculate_rank_probabilities(
            total_rooms,
            floors,
            pressure_override,
        )
        room_type = getattr(node, "room_type", "") or ""
        forced_prime = "prime" in room_type
        forced_glitched = "glitched" in room_type
        party_ids = {p.id for p in party.members}
        if exclude_ids:
            party_ids.update(str(eid) for eid in exclude_ids if eid)
        recent_set = {str(rid) for rid in (recent_ids or []) if rid}

        if "boss" in room_type:
            template = self._choose_template(
                node,
                party_ids,
                recent_set,
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
            return [foe]

        desired = self._desired_count(node, party)
        templates = self._sample_templates(
            desired,
            node,
            party_ids,
            recent_set,
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
            foes.append(foe)
        return foes

    def _sample_templates(
        self,
        count: int,
        node: MapNode,
        party_ids: Collection[str],
        recent_ids: Collection[str],
    ) -> list[SpawnTemplate]:
        pool = [
            template
            for template in self._templates.values()
            if template.id not in party_ids
        ]
        if not pool:
            return []
        unique: dict[str, SpawnTemplate] = {}
        for template in pool:
            unique.setdefault(template.id, template)
        candidates = list(unique.values())
        weights: list[float] = []
        for template in candidates:
            weight = self._weight_for_template(
                template,
                node=node,
                party_ids=party_ids,
                recent_ids=recent_ids,
                boss=False,
            )
            if template.id in recent_ids and weight > 0:
                factor = self.config["recent_weight_factor"]
                minimum = self.config["recent_weight_min"]
                weight = max(weight * factor, minimum)
            weights.append(max(weight, 0.0))
        selected: list[SpawnTemplate] = []
        candidate_weights = weights[:]
        for _ in range(min(count, len(candidates))):
            if not candidates:
                break
            if not any(weight > 0 for weight in candidate_weights):
                candidate_weights = [1.0 for _ in candidates]
            choice = random.choices(candidates, weights=candidate_weights, k=1)[0]
            selected.append(choice)
            idx = candidates.index(choice)
            candidates.pop(idx)
            candidate_weights.pop(idx)
        return selected

    def _choose_template(
        self,
        node: MapNode,
        party_ids: Collection[str],
        recent_ids: Collection[str],
        *,
        boss: bool,
    ) -> SpawnTemplate | None:
        candidates = [
            template
            for template in self._templates.values()
            if template.id not in party_ids
        ]
        if not candidates:
            return None
        weights = [
            max(
                self._weight_for_template(
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
        if not any(weight > 0 for weight in weights):
            weights = [1.0 for _ in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]

    def _desired_count(self, node: MapNode, party: Party) -> int:
        base_cap = int(self.config["base_spawn_cap"])
        pressure_base = int(self.config["pressure_spawn_base"])
        pressure_step = int(self.config["pressure_spawn_step"])
        base = min(base_cap, pressure_base + max(node.pressure, 0) // max(pressure_step, 1))
        extras = 0
        size = len(party.members)
        max_extra = max(size - 1, 0)
        if max_extra:
            if random.random() < float(self.config["party_extra_full_chance"]):
                extras = max_extra
            else:
                for tier in range(max_extra - 1, 0, -1):
                    if random.random() < float(self.config["party_extra_step_chance"]):
                        extras = tier
                        break
        return min(base_cap, base + extras)

    @staticmethod
    def calculate_rank_probabilities(
        total_rooms_cleared: int = 0,
        floors_cleared: int = 0,
        pressure: int = 0,
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
        pressure_bonus = pressure_value * 0.01
        total_rate = scaled_rate + pressure_bonus
        chance = 1.0 if total_rate >= 1.0 else max(total_rate, 0.0)
        return chance, chance

    def scale_stats(self, obj: Stats, node: MapNode, strength: float = 1.0) -> None:
        starter_int = 1.0 + random.uniform(-self.config["scaling_variance"], self.config["scaling_variance"])
        cumulative_rooms = (node.floor - 1) * MapGenerator.rooms_per_floor + node.index
        room_mult = starter_int + self.config["room_growth_multiplier"] * max(cumulative_rooms - 1, 0)
        loop_mult = starter_int + self.config["loop_growth_multiplier"] * max(node.loop - 1, 0)
        pressure_mult = self.config["pressure_multiplier"] * max(node.pressure, 1)
        base_mult = max(strength * room_mult * loop_mult * pressure_mult, 0.5)

        foe_debuff = self.config["foe_base_debuff"] if isinstance(obj, FoeBase) else 1.0
        apply_permanent_scaling(
            obj,
            multipliers={"atk": foe_debuff, "max_hp": foe_debuff},
            name="Base foe debuff",
            modifier_id=self.config["base_debuff_id"],
        )
        if isinstance(obj, FoeBase):
            apply_permanent_scaling(
                obj,
                multipliers={"defense": min((foe_debuff * node.floor) / 4, 1.0)},
                name="Base foe defense debuff",
                modifier_id=f"{self.config['base_debuff_id']}_defense",
            )

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
        multipliers = {}
        for field_info in fields(type(obj)):
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
            value = getattr(obj, target_name, None)
            if isinstance(value, (int, float)):
                per_stat_variation = 1.0 + random.uniform(-self.config["scaling_variance"], self.config["scaling_variance"])
                multipliers[target_name] = base_mult * per_stat_variation
        apply_permanent_scaling(
            obj,
            multipliers=multipliers,
            name="Room scaling",
            modifier_id=self.config["scaling_modifier_id"],
        )

        try:
            room_num = max(int(cumulative_rooms), 1)
            desired = max(1, int(room_num / 2))
            obj.level = int(max(getattr(obj, "level", 1), desired))
        except Exception:
            pass

        try:
            room_num = max(int(node.index), 1)
            base_hp = int(15 * room_num * (foe_debuff if isinstance(obj, FoeBase) else 1.0))
            low = int(base_hp * 0.85)
            high = int(base_hp * 1.10)
            target = random.randint(low, max(high, low + 1))
            current_max = int(getattr(obj, "max_hp", 1))
            new_max = max(current_max, target)
            obj.set_base_stat("max_hp", new_max)
            obj.hp = new_max
        except Exception:
            pass

        try:
            cd = getattr(obj, "crit_damage", None)
            if isinstance(cd, (int, float)):
                obj.set_base_stat("crit_damage", max(float(cd), 2.0))
        except Exception:
            pass

        if isinstance(obj, FoeBase):
            try:
                er = getattr(obj, "effect_resistance", None)
                if isinstance(er, (int, float)):
                    obj.set_base_stat("effect_resistance", max(0.0, float(er)))
            except Exception:
                pass
            try:
                apt = getattr(obj, "actions_per_turn", None)
                if isinstance(apt, (int, float)):
                    obj.actions_per_turn = int(
                        min(max(1, int(apt)), int(self.config["max_actions_per_turn"]))
                    )
            except Exception:
                pass
            try:
                ap = getattr(obj, "action_points", None)
                if isinstance(ap, (int, float)):
                    obj.action_points = int(
                        min(max(0, int(ap)), int(self.config["max_action_points"]))
                    )
            except Exception:
                pass

        try:
            if isinstance(obj, FoeBase):
                d = getattr(obj, "defense", None)
                if isinstance(d, (int, float)):
                    override = getattr(obj, "min_defense_override", None)
                    if isinstance(override, (int, float)):
                        min_def = max(int(override), 0)
                    else:
                        min_def = 2 + cumulative_rooms
                    if d < min_def:
                        obj.set_base_stat("defense", min_def)
        except Exception:
            pass

        try:
            if isinstance(obj, FoeBase) and node.pressure > 0:
                d = getattr(obj, "defense", None)
                if isinstance(d, (int, float)):
                    base_def = node.pressure * self.config["pressure_defense_floor"]
                    min_factor = float(self.config["pressure_defense_min_roll"])
                    max_factor = float(self.config["pressure_defense_max_roll"])
                    random_factor = random.uniform(min_factor, max_factor)
                    pressure_defense = int(base_def * random_factor)
                    if pressure_defense > d:
                        obj.set_base_stat("defense", pressure_defense)
        except Exception:
            pass

        for attr, thr, step, base in (
            ("vitality", 0.5, 0.25, 5.0),
            ("mitigation", 0.2, 0.01, 5.0),
        ):
            try:
                if isinstance(obj, FoeBase):
                    value = getattr(obj, attr, None)
                    if isinstance(value, (int, float)):
                        fval = float(value)
                        if fval < thr:
                            fval = thr
                        else:
                            excess = fval - thr
                            steps = int(excess // step)
                            factor = base + steps
                            fval = thr + (excess / factor)
                            fval = max(fval, thr)
                        obj.set_base_stat(attr, fval)
            except Exception:
                pass


_FACTORY: FoeFactory | None = None


def get_foe_factory() -> FoeFactory:
    global _FACTORY
    if _FACTORY is None:
        _FACTORY = FoeFactory()
    return _FACTORY

