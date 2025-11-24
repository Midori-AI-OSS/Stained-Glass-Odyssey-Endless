from dataclasses import dataclass
from typing import Any
from typing import ClassVar

from autofighter.effects import DamageOverTime
from autofighter.stats import BUS
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


class WindTurnSpread:
    """Helper coordinating Wind's multi-target turn spread behavior."""

    __slots__ = ()

    def collect_targets(
        self,
        context: Any,
        target_index: int,
        target_foe: Any,
    ) -> list[tuple[Any, Any]]:
        from autofighter.rooms.battle.turn_loop.player_turn import (
            _collect_wind_spread_targets,
        )

        return _collect_wind_spread_targets(context, target_index, target_foe)

    async def resolve(
        self,
        context: Any,
        member: Any,
        target_index: int,
        *,
        additional_targets: list[tuple[Any, Any]] | None = None,
        per_duration: float | None = None,
    ) -> int:
        from autofighter.rooms.battle.turn_loop.player_turn import _handle_wind_spread

        return await _handle_wind_spread(
            context,
            member,
            target_index,
            additional_targets=additional_targets,
            per_duration=per_duration,
        )


_WIND_TURN_SPREAD = WindTurnSpread()


@dataclass
class Wind(DamageTypeBase):
    """Agile element that strikes in flurries and erodes defenses."""
    id: str = "Wind"
    weakness: str = "Lightning"
    color: tuple[int, int, int] = (0, 255, 0)
    _players: ClassVar[list] = []
    _foes: ClassVar[list] = []
    _pending: ClassVar[list] = []
    _initialized: ClassVar[bool] = False

    def __post_init__(self) -> None:
        # Ensure we only subscribe once at the class level
        if not Wind._initialized:
            BUS.subscribe("battle_start", Wind._on_battle_start)
            BUS.subscribe("battle_end", Wind._on_battle_end)
            Wind._initialized = True

    # Previous implementation scattered DoTs after an ultimate by moving
    # existing effects. The new design: when Wind uses its ultimate, strike
    # every living foe multiple times and temporarily increase the user's
    # effect hit rate so Gale Erosion applies more reliably. The number of hits
    # is derived dynamically (from actor.wind_ultimate_hits or actor.ultimate_hits)
    # to allow relics/cards to adjust it.

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    def get_turn_spread(self) -> WindTurnSpread:
        """Expose Wind's normal-action spread helper to the turn loop."""

        return _WIND_TURN_SPREAD

    async def ultimate(self, actor, allies, enemies):
        """Distribute attack across rapid hits on all foes.

        Deprecated wrapper that now routes through the Wind ultimate action.
        """

        from plugins.actions.ultimate.utils import run_ultimate_action
        from plugins.actions.ultimate.wind_ultimate import WindUltimate

        result = await run_ultimate_action(WindUltimate, actor, allies, enemies)
        return bool(getattr(result, "success", False))

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Temporarily boosts the user's effect hit rate, then splits their attack "
            "into repeated strikes distributed across all living enemies. The number "
            "of hits derives from `wind_ultimate_hits` or `ultimate_hits` allowing "
            "relics and cards to modify it. Each hit respects TURN_PACING via the "
            "battle pacing helper."
        )

    @classmethod
    def _on_battle_start(cls, actor) -> None:
        """Register actors into appropriate lists when battle starts."""
        # Only register actors with Wind damage type
        actor_damage_type = getattr(actor, "damage_type", None)
        if not isinstance(actor_damage_type, Wind):
            return

        # Determine actor type and add to appropriate registry
        actor_type = getattr(actor, "plugin_type", None)
        if actor_type == "player":
            if actor not in cls._players:
                cls._players.append(actor)
        elif actor_type == "foe":
            if actor not in cls._foes:
                cls._foes.append(actor)

    @classmethod
    def _on_battle_end(cls, *_: object) -> None:
        """Clear all registries when battle ends."""
        cls._players.clear()
        cls._foes.clear()
        cls._pending.clear()
