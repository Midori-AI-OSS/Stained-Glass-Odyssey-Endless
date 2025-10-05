from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Mapping

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from services.run_configuration import RunModifierContext

    from .party import Party


@dataclass
class MapNode:
    room_id: int
    room_type: str
    floor: int
    index: int
    loop: int
    pressure: int
    metadata_hash: str | None = None
    modifier_context: Mapping[str, Any] | None = None
    encounter_bonus: int = 0
    encounter_bonus_marker: bool = False
    elite_bonus_pct: float = 0.0
    prime_bonus_pct: float = 0.0
    glitched_bonus_pct: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MapNode:
        # Provide default values for missing fields to handle legacy data
        return cls(
            room_id=data.get('room_id', 0),
            room_type=data.get('room_type', 'battle-weak'),
            floor=data.get('floor', 1),
            index=data.get('index', 0),
            loop=data.get('loop', 1),
            pressure=data.get('pressure', 0),
            metadata_hash=data.get('metadata_hash'),
            modifier_context=data.get('modifier_context'),
            encounter_bonus=int(data.get('encounter_bonus', 0) or 0),
            encounter_bonus_marker=bool(data.get('encounter_bonus_marker', False)),
            elite_bonus_pct=float(data.get('elite_bonus_pct', 0.0) or 0.0),
            prime_bonus_pct=float(data.get('prime_bonus_pct', 0.0) or 0.0),
            glitched_bonus_pct=float(data.get('glitched_bonus_pct', 0.0) or 0.0),
        )


class MapGenerator:
    rooms_per_floor: ClassVar[int] = 10

    def __init__(
        self,
        seed: str,
        *,
        floor: int = 1,
        loop: int = 1,
        pressure: int = 0,
        modifier_context: "RunModifierContext | Mapping[str, Any] | None" = None,
        configuration: Mapping[str, Any] | None = None,
    ) -> None:
        self._rand = Random(seed)
        self.floor = floor
        self.loop = loop
        self.pressure = pressure
        self._raw_context: Mapping[str, Any] | None = None
        self._context: "RunModifierContext | None" = None
        if modifier_context is not None:
            context_dict: Mapping[str, Any] | None = None
            if hasattr(modifier_context, "to_dict"):
                try:
                    context_dict = modifier_context.to_dict()  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover - defensive
                    context_dict = None
            elif isinstance(modifier_context, Mapping):
                context_dict = dict(modifier_context)

            if context_dict is not None:
                self._raw_context = context_dict
            try:
                from services.run_configuration import (
                    RunModifierContext,  # local import to avoid cycle
                )

                if isinstance(modifier_context, RunModifierContext):
                    self._context = modifier_context
                    self.pressure = modifier_context.pressure
                    if self._raw_context is None:
                        self._raw_context = modifier_context.to_dict()
                elif context_dict is not None:
                    self._context = RunModifierContext.from_dict(context_dict)
                    self.pressure = self._context.pressure
            except Exception:  # pragma: no cover - defensive import guard
                pass
        self.configuration = dict(configuration or {})
        self._room_overrides: dict[str, dict[str, Any]] = {}
        if self.configuration:
            try:
                from services.run_configuration import get_room_overrides

                self._room_overrides = get_room_overrides(self.configuration)
            except Exception:
                self._room_overrides = {}

    def generate_floor(self, party: Party | None = None) -> list[MapNode]:
        if self._is_boss_rush(party):
            return self._generate_boss_rush_floor()

        nodes: list[MapNode] = []
        index = 0
        context = self._context
        metadata_hash = self._raw_context.get("metadata_hash") if self._raw_context else None
        encounter_bonus = 0
        elite_bonus_pct = 0.0
        prime_bonus_pct = 0.0
        glitched_bonus_pct = 0.0
        if context is not None:
            try:
                encounter_bonus = max(int(context.encounter_slot_bonus), 0)
            except Exception:
                encounter_bonus = 0
            try:
                elite_bonus_pct = max(float(context.elite_spawn_bonus_pct), 0.0)
            except Exception:
                elite_bonus_pct = 0.0
            try:
                prime_bonus_pct = max(float(context.prime_spawn_bonus_pct), 0.0)
            except Exception:
                prime_bonus_pct = 0.0
            try:
                glitched_bonus_pct = max(float(context.glitched_spawn_bonus_pct), 0.0)
            except Exception:
                glitched_bonus_pct = 0.0

        prime_stacks = 0
        glitched_stacks = 0
        try:
            from services.run_configuration import (
                get_modifier_snapshot,  # local import to avoid cycle
            )

            prime_summary = get_modifier_snapshot(self.configuration, "foe_prime_rate")
            glitched_summary = get_modifier_snapshot(self.configuration, "foe_glitched_rate")
            prime_stacks = max(int(prime_summary.get("stacks", 0) or 0), 0)
            glitched_stacks = max(int(glitched_summary.get("stacks", 0) or 0), 0)
        except Exception:
            prime_stacks = 0
            glitched_stacks = 0

        nodes.append(
            MapNode(
                room_id=index,
                room_type="start",
                floor=self.floor,
                index=index,
                loop=self.loop,
                pressure=self.pressure,
                metadata_hash=metadata_hash,
                modifier_context=self._raw_context,
                encounter_bonus=0,
                elite_bonus_pct=elite_bonus_pct,
                prime_bonus_pct=prime_bonus_pct,
                glitched_bonus_pct=glitched_bonus_pct,
            )
        )
        index += 1
        middle = self.rooms_per_floor - 2
        suppressed: set[str] = {
            room_type
            for room_type, override in self._room_overrides.items()
            if not override.get("enabled", True)
        }
        if self._disable_room("shop", party):
            suppressed.add("shop")
        if self._disable_room("rest", party):
            suppressed.add("rest")
        if party is not None:
            relics = getattr(party, "relics", [])
            if isinstance(relics, list) and "null_lantern" in relics:
                suppressed.update({"shop", "rest"})

        quotas: dict[str, int] = {}
        remaining_optional_slots = middle

        def _apply_quota(room_type: str, default: int | None = None) -> None:
            nonlocal remaining_optional_slots
            if room_type in suppressed:
                return
            quota_value = self._room_quota(room_type, default)
            if quota_value is None or quota_value <= 0:
                return
            allowed = min(int(quota_value), remaining_optional_slots)
            if allowed <= 0:
                return
            quotas[room_type] = allowed
            remaining_optional_slots -= allowed

        _apply_quota("shop", default=1)
        _apply_quota("rest")
        for room_type in self._room_overrides:
            if room_type in {"shop", "rest"}:
                continue
            _apply_quota(room_type)
        room_types: list[str] = []
        for key, count in quotas.items():
            room_types.extend([key] * count)
        battle_count = middle - sum(quotas.values())
        if battle_count < 0:
            battle_count = 0

        normal = battle_count // 2
        weak = battle_count - normal
        if encounter_bonus:
            normal = min(battle_count, normal + encounter_bonus)
            weak = max(battle_count - normal, 0)

        prime_rooms = 0
        if prime_stacks:
            prime_rooms = min(normal, max(prime_stacks // 2, 1))
        elif prime_bonus_pct:
            prime_rooms = min(normal, int(prime_bonus_pct // 15))

        glitched_rooms = 0
        remaining_slots = normal - prime_rooms
        if glitched_stacks and remaining_slots > 0:
            glitched_rooms = min(remaining_slots, max(glitched_stacks // 2, 1))
        elif glitched_bonus_pct and remaining_slots > 0:
            glitched_rooms = min(remaining_slots, int(glitched_bonus_pct // 20))

        battle_types: list[str] = []
        battle_types.extend(["battle-prime"] * prime_rooms)
        battle_types.extend(["battle-glitched"] * glitched_rooms)
        battle_types.extend(["battle-normal"] * max(normal - prime_rooms - glitched_rooms, 0))
        battle_types.extend(["battle-weak"] * weak)

        self._rand.shuffle(battle_types)
        bonus_flags = [True] * min(encounter_bonus, len(battle_types))
        bonus_flags.extend([False] * max(len(battle_types) - len(bonus_flags), 0))
        if bonus_flags:
            self._rand.shuffle(bonus_flags)
        battle_pairs = list(zip(battle_types, bonus_flags or [False] * len(battle_types)))

        if room_types and room_types[0] == "shop":
            for i, rt in enumerate(room_types[1:], start=1):
                if rt != "shop":
                    room_types[0], room_types[i] = room_types[i], room_types[0]
                    break
        if suppressed:
            filtered = [rt for rt in room_types if rt not in suppressed]
            removed = len(room_types) - len(filtered)
            if removed:
                replacements: list[str] = []
                for i in range(removed):
                    replacements.append("battle-weak" if i % 2 == 0 else "battle-normal")
                filtered.extend(replacements)
                self._rand.shuffle(filtered)
            room_types = filtered[:middle]
        while len(room_types) < middle:
            room_types.append("battle-normal" if len(room_types) % 2 else "battle-weak")

        battle_iter = iter(battle_pairs)
        enriched_types: list[tuple[str, bool]] = []
        for rt in room_types:
            if rt.startswith("battle"):
                try:
                    enriched_types.append(next(battle_iter))
                except StopIteration:
                    enriched_types.append((rt, False))
            else:
                enriched_types.append((rt, False))

        for rt, bonus in enriched_types:
            nodes.append(
                MapNode(
                    room_id=index,
                    room_type=rt,
                    floor=self.floor,
                    index=index,
                    loop=self.loop,
                    pressure=self.pressure,
                    metadata_hash=metadata_hash,
                    modifier_context=self._raw_context,
                    encounter_bonus=0,
                    encounter_bonus_marker=bool(bonus) if rt.startswith("battle") else False,
                    elite_bonus_pct=elite_bonus_pct,
                    prime_bonus_pct=prime_bonus_pct,
                    glitched_bonus_pct=glitched_bonus_pct,
                )
            )
            index += 1
        nodes.append(
            MapNode(
                room_id=index,
                room_type="battle-boss-floor",
                floor=self.floor,
                index=index,
                loop=self.loop,
                pressure=self.pressure,
                metadata_hash=metadata_hash,
                modifier_context=self._raw_context,
                encounter_bonus=0,
                elite_bonus_pct=elite_bonus_pct,
                prime_bonus_pct=prime_bonus_pct,
                glitched_bonus_pct=glitched_bonus_pct,
            )
        )
        return nodes

    def _generate_boss_rush_floor(self) -> list[MapNode]:
        nodes: list[MapNode] = []
        metadata_hash = self._raw_context.get("metadata_hash") if self._raw_context else None
        context = self._context
        elite_bonus_pct = 0.0
        prime_bonus_pct = 0.0
        glitched_bonus_pct = 0.0
        if context is not None:
            try:
                elite_bonus_pct = max(float(context.elite_spawn_bonus_pct), 0.0)
            except Exception:
                elite_bonus_pct = 0.0
            try:
                prime_bonus_pct = max(float(context.prime_spawn_bonus_pct), 0.0)
            except Exception:
                prime_bonus_pct = 0.0
            try:
                glitched_bonus_pct = max(float(context.glitched_spawn_bonus_pct), 0.0)
            except Exception:
                glitched_bonus_pct = 0.0
        for index in range(self.rooms_per_floor):
            room_type = "start" if index == 0 else "battle-boss-floor"
            nodes.append(
                MapNode(
                    room_id=index,
                    room_type=room_type,
                    floor=self.floor,
                    index=index,
                    loop=self.loop,
                    pressure=self.pressure,
                    metadata_hash=metadata_hash,
                    modifier_context=self._raw_context,
                    encounter_bonus=0,
                    elite_bonus_pct=elite_bonus_pct,
                    prime_bonus_pct=prime_bonus_pct,
                    glitched_bonus_pct=glitched_bonus_pct,
                )
            )
        return nodes

    @staticmethod
    def _party_requests_boss_rush(party: Party) -> bool:
        config = getattr(party, "run_config", None)
        if isinstance(config, dict):
            run_type = config.get("run_type")
            if isinstance(run_type, dict):
                if run_type.get("id") == "boss_rush":
                    return True
            elif isinstance(run_type, str) and run_type == "boss_rush":
                return True
        return bool(getattr(party, "boss_rush", False))

    def _is_boss_rush(self, party: Party | None) -> bool:
        run_type_entry = self.configuration.get("run_type")
        run_type_id: str | None = None
        if isinstance(run_type_entry, Mapping):
            candidate = run_type_entry.get("id")
            if isinstance(candidate, str):
                run_type_id = candidate
        elif isinstance(run_type_entry, str):
            run_type_id = run_type_entry

        if run_type_id == "boss_rush":
            return True

        if party is not None:
            return self._party_requests_boss_rush(party)
        return False

    def _room_enabled(self, room_type: str) -> bool:
        override = self._room_overrides.get(room_type)
        if override is None:
            return True
        return bool(override.get("enabled", True))

    def _room_quota(self, room_type: str, default: int | None = None) -> int | None:
        override = self._room_overrides.get(room_type)
        if override is None:
            return default
        if not bool(override.get("enabled", True)):
            return 0
        count = override.get("count")
        if count is None:
            return default
        try:
            numeric = int(count)
        except (TypeError, ValueError):
            return default
        if numeric <= 0:
            return 0
        return numeric

    def _disable_room(self, room_type: str, party: Party | None) -> bool:
        if not self._room_enabled(room_type):
            return True
        run_type = self.configuration.get("run_type")
        run_type_id: str | None = None
        if isinstance(run_type, Mapping):
            candidate = run_type.get("id")
            if isinstance(candidate, str):
                run_type_id = candidate
        elif isinstance(run_type, str):
            run_type_id = run_type

        if run_type_id == "boss_rush" and room_type in {"shop", "rest"}:
            return True

        if party is not None:
            flag_name = f"no_{room_type}s"
            if getattr(party, flag_name, False):
                return True
        return False
