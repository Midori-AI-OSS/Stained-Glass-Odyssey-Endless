import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
import logging
from typing import Any

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.party import Party

log = logging.getLogger(__name__)


def safe_async_task(coro):
    """Safely create an async task, handling cases where no event loop is running."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        return loop.create_task(coro)
    except RuntimeError:
        # No event loop running, create a new one and run the coroutine
        try:
            return asyncio.run(coro)
        except Exception as e:
            log.warning("Failed to execute async operation: %s", e)
            return None


@dataclass
class CardBase:
    plugin_type = "card"

    id: str = ""
    name: str = ""
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = ""
    _subscriptions: "SubscriptionRegistry" = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        self._subscriptions = SubscriptionRegistry()
        if not self.about and self.effects:
            parts: list[str] = []
            for attr, pct in self.effects.items():
                sign = "+" if pct >= 0 else ""
                pretty = attr.replace("_", " ")
                parts.append(f"{sign}{pct * 100:.0f}% {pretty}")
            self.about = ", ".join(parts)

    async def apply(self, party: Party) -> None:
        from autofighter.stats import BUS  # Import here to avoid circular imports

        log.info("Applying card %s to party", self.id)
        for member in party.members:
            log.debug("Applying effects to %s", getattr(member, "id", "member"))
            mgr = getattr(member, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(member)
                member.effect_manager = mgr
            for attr, pct in self.effects.items():
                changes = {f"{attr}_mult": 1 + pct}
                mod = create_stat_buff(
                    member, name=f"{self.id}_{attr}", turns=9999, **changes
                )
                mgr.add_modifier(mod)

                # Emit card effect event
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    member,
                    f"stat_buff_{attr}",
                    int(pct * 100),
                    {
                        "stat_affected": attr,
                        "percentage_change": pct * 100,
                        "new_modifier": f"{self.id}_{attr}",
                    },
                )

                if attr == "max_hp":
                    heal = int(getattr(member, "hp", 0) * pct)
                    try:
                        asyncio.get_running_loop()
                    except RuntimeError:
                        await member.apply_healing(heal)
                    else:
                        asyncio.create_task(member.apply_healing(heal))

                    # Emit card healing event
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        member,
                        "healing",
                        heal,
                        {
                            "heal_amount": heal,
                            "heal_type": "max_hp_increase",
                        },
                    )

                    log.debug(
                        "Updated %s max_hp and healed %s",
                        getattr(member, "id", "member"),
                        heal,
                    )
                else:
                    log.debug(
                        "Updated %s %s via stat modifier",
                        getattr(member, "id", "member"),
                        attr,
                    )

    def subscribe(
        self,
        event: str,
        callback: Callable[..., Any],
        *,
        cleanup_event: str | None = "battle_end",
    ) -> Callable[..., Any]:
        """Register an event handler that automatically cleans up."""
        self._subscriptions.subscribe(event, callback, cleanup_event=cleanup_event)
        return callback

    def unsubscribe(self, event: str, callback: Callable[..., Any]) -> None:
        """Remove a specific event handler from the registry."""
        self._subscriptions.unsubscribe(event, callback)

    def cleanup_subscriptions(self) -> None:
        """Remove all tracked subscriptions."""
        self._subscriptions.clear()


class SubscriptionRegistry:
    """Track event bus subscriptions for a card instance."""

    def __init__(self) -> None:
        self._entries: list[tuple[str, Callable[..., Any]]] = []
        self._cleanup_handlers: dict[str, Callable[..., Any]] = {}

    def subscribe(
        self,
        event: str,
        callback: Callable[..., Any],
        cleanup_event: str | None = "battle_end",
    ) -> None:
        from autofighter.stats import BUS

        BUS.subscribe(event, callback)
        self._entries.append((event, callback))
        if cleanup_event:
            self._ensure_cleanup_handler(cleanup_event)

    def unsubscribe(self, event: str, callback: Callable[..., Any]) -> None:
        from autofighter.stats import BUS

        BUS.unsubscribe(event, callback)
        self._entries = [
            (evt, cb)
            for evt, cb in self._entries
            if evt != event or cb is not callback
        ]

    def clear(self, *, remove_cleanup_handlers: bool = True) -> None:
        from autofighter.stats import BUS

        for event, callback in list(self._entries):
            BUS.unsubscribe(event, callback)
        self._entries.clear()

        if remove_cleanup_handlers:
            for event in list(self._cleanup_handlers):
                self._remove_cleanup_handler(event)

    def _ensure_cleanup_handler(self, event: str) -> None:
        from autofighter.stats import BUS

        if event in self._cleanup_handlers:
            handler = self._cleanup_handlers[event]
            BUS.unsubscribe(event, handler)
            BUS.subscribe(event, handler)
            return

        def _cleanup_handler(*_: object) -> None:
            self.clear(remove_cleanup_handlers=False)
            self._remove_cleanup_handler(event)

        self._cleanup_handlers[event] = _cleanup_handler
        BUS.subscribe(event, _cleanup_handler)

    def _remove_cleanup_handler(self, event: str) -> None:
        handler = self._cleanup_handlers.pop(event, None)
        if handler is None:
            return

        from autofighter.stats import BUS

        BUS.unsubscribe(event, handler)
