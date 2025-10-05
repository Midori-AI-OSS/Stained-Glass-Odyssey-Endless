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
                from services.run_configuration import RunModifierContext  # local import to avoid cycle

                if isinstance(modifier_context, RunModifierContext):
                    self.pressure = modifier_context.pressure
                    if self._raw_context is None:
                        self._raw_context = modifier_context.to_dict()
            except Exception:  # pragma: no cover - defensive import guard
                pass
        self.configuration = dict(configuration or {})

    def generate_floor(self, party: Party | None = None) -> list[MapNode]:
        if self._is_boss_rush(party):
            return self._generate_boss_rush_floor()

        nodes: list[MapNode] = []
        index = 0
        nodes.append(
            MapNode(
                room_id=index,
                room_type="start",
                floor=self.floor,
                index=index,
                loop=self.loop,
                pressure=self.pressure,
                metadata_hash=self._raw_context.get("metadata_hash") if self._raw_context else None,
                modifier_context=self._raw_context,
            )
        )
        index += 1
        middle = self.rooms_per_floor - 2
        suppressed: set[str] = set()
        if self._disable_room("shop", party):
            suppressed.add("shop")
        if self._disable_room("rest", party):
            suppressed.add("rest")
        if party is not None:
            relics = getattr(party, "relics", [])
            if isinstance(relics, list) and "null_lantern" in relics:
                suppressed.update({"shop", "rest"})

        quotas: dict[str, int] = {}
        if "shop" not in suppressed:
            quotas["shop"] = 1
        room_types: list[str] = []
        for key, count in quotas.items():
            room_types.extend([key] * count)
        battle_count = middle - sum(quotas.values())
        weak = battle_count // 2
        normal = battle_count - weak
        room_types.extend(["battle-weak"] * weak)
        room_types.extend(["battle-normal"] * normal)
        self._rand.shuffle(room_types)
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
        for rt in room_types:
            nodes.append(
                MapNode(
                    room_id=index,
                    room_type=rt,
                    floor=self.floor,
                    index=index,
                    loop=self.loop,
                    pressure=self.pressure,
                    metadata_hash=self._raw_context.get("metadata_hash") if self._raw_context else None,
                    modifier_context=self._raw_context,
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
                metadata_hash=self._raw_context.get("metadata_hash") if self._raw_context else None,
                modifier_context=self._raw_context,
            )
        )
        return nodes

    def _generate_boss_rush_floor(self) -> list[MapNode]:
        nodes: list[MapNode] = []
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
                    metadata_hash=self._raw_context.get("metadata_hash") if self._raw_context else None,
                    modifier_context=self._raw_context,
                )
            )
        return nodes

    @staticmethod
    def _is_boss_rush(party: Party) -> bool:
        config = getattr(party, "run_config", None)
        if isinstance(config, dict):
            run_type = config.get("run_type")
            if isinstance(run_type, dict):
                if run_type.get("id") == "boss_rush":
                    return True
            elif isinstance(run_type, str) and run_type == "boss_rush":
                return True
        return bool(getattr(party, "boss_rush", False))

    def _disable_room(self, room_type: str, party: Party | None) -> bool:
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
