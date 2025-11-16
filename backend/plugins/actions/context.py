"""Battle context wrapper shared by plugin actions."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any
from typing import Sequence

from autofighter.effects import EffectManager
from autofighter.summons.manager import SummonManager
from plugins.event_bus import EventBus

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from autofighter.passives import PassiveRegistry
    from autofighter.rooms.battle.enrage import EnrageState
    from autofighter.stats import Stats
    from plugins.damage_types._base import DamageTypeBase

    from .registry import ActionRegistry


@dataclass(slots=True)
class BattleContext:
    """Runtime information that action plugins need to operate safely."""

    turn: int
    run_id: str
    phase: str
    actor: "Stats"
    allies: Sequence["Stats"]
    enemies: Sequence["Stats"]
    action_registry: "ActionRegistry"
    passive_registry: "PassiveRegistry"
    effect_managers: dict[str, EffectManager] = field(default_factory=dict)
    summon_manager: SummonManager | None = None
    event_bus: EventBus | None = None
    enrage_state: "EnrageState" | None = None
    visual_queue: Any | None = None
    damage_router: Any | None = None

    def effect_manager_for(self, target: "Stats") -> EffectManager:
        """Return the cached :class:`EffectManager` for *target*.

        Battle setup pre-populates :attr:`effect_managers` for all combatants,
        but plugin actions may also request managers for fresh summons. When the
        lookup fails the method creates a new :class:`EffectManager` so callers
        do not have to coordinate with the owning system.
        """

        key = self._key_for(target)
        manager = self.effect_managers.get(key)
        if manager is None:
            manager = EffectManager(target)
            self.effect_managers[key] = manager
        return manager

    async def apply_damage(
        self,
        attacker: "Stats",
        target: "Stats",
        amount: float,
        *,
        damage_type: "DamageTypeBase" | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Apply damage via the standard battle pipeline.

        This placeholder defers to the existing helpers in
        :mod:`autofighter.rooms.battle.resolution`. A follow-up task will wire
        those helpers into this method.
        """

        raise NotImplementedError("Damage resolution will be wired up in task 4afe1e97")

    async def apply_healing(
        self,
        healer: "Stats",
        target: "Stats",
        amount: float,
        *,
        overheal_allowed: bool = False,
    ) -> int:
        """Apply healing through the shared battle helpers."""

        raise NotImplementedError("Healing resolution will be wired up in task 4afe1e97")

    def spend_resource(self, actor: "Stats", resource: str, amount: int) -> None:
        """Deduct a resource from *actor*.

        The default implementation handles the built-in stats. Services that
        expose custom pools can override this method when constructing the
        context.
        """

        if resource == "ultimate_charge":
            actor.ultimate_charge = max(actor.ultimate_charge - amount, 0)
        elif resource == "action_points":
            actor.action_points = max(actor.action_points - amount, 0)
        else:
            current = getattr(actor, resource, 0)
            setattr(actor, resource, max(int(current) - amount, 0))

    async def emit_action_event(self, event: str, *args, **kwargs) -> None:
        """Proxy helper that yields to :class:`plugins.event_bus.EventBus`."""

        if self.event_bus is None:
            return
        await self.event_bus.emit_async(event, *args, **kwargs)

    def allies_of(self, actor: "Stats") -> Sequence["Stats"]:
        """Return the ally list for *actor* within the current phase."""

        if actor in self.allies:
            return self.allies
        if actor in self.enemies:
            return self.enemies
        return self.allies

    def enemies_of(self, actor: "Stats") -> Sequence["Stats"]:
        """Return the opposing team for *actor*."""

        if actor in self.allies:
            return self.enemies
        if actor in self.enemies:
            return self.allies
        return self.enemies

    @staticmethod
    def _key_for(target: "Stats") -> str:
        return str(getattr(target, "id", id(target)))
