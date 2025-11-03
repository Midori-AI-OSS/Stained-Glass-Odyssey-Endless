import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
import logging
from typing import ClassVar
from typing import Sequence

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.party import Party
from autofighter.reward_preview import RewardPreviewPayload
from autofighter.reward_preview import RewardPreviewTrigger
from autofighter.reward_preview import build_preview_from_effects

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
class RelicBase:
    plugin_type = "relic"

    id: str = ""
    name: str = ""
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = "Missing full relic description, please report this"
    summarized_about: str = "Missing summarized relic description, please report this"
    preview_triggers: ClassVar[Sequence[RewardPreviewTrigger | dict[str, object]]] = ()

    async def apply(self, party: Party) -> None:
        from autofighter.stats import BUS  # Import here to avoid circular imports

        self._reset_subscriptions(party)
        log.info("Applying relic %s to party", self.id)
        mods = []
        stacks = party.relics.count(self.id)

        for member in party.members:
            log.debug("Applying relic to %s", getattr(member, "id", "member"))
            mgr = getattr(member, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(member)
                member.effect_manager = mgr

            # Apply stack multiplier to effects: each additional copy multiplies the effect
            changes = {f"{attr}_mult": (1 + pct) ** stacks for attr, pct in self.effects.items()}
            if not changes:
                continue
            mod = create_stat_buff(member, name=self.id, turns=9999, **changes)
            await mgr.add_modifier(mod)
            mods.append(mod)

            # Emit relic effect tracking for stat modifications
            for attr, pct in self.effects.items():
                await BUS.emit_async("relic_effect", self.id, member, f"stat_buff_{attr}", int(pct * 100), {
                    "stat_affected": attr,
                    "percentage_change": pct * 100,
                    "stacks": stacks,
                    "cumulative_effect": (1 + pct) ** stacks - 1 if stacks > 1 else pct,
                    "modifier_name": self.id
                })

        self._mods = mods

    def remove(self) -> None:
        for mod in getattr(self, "_mods", []):
            mod.remove()
        self._mods = []

    def get_about_str(self) -> str:
        """Return the appropriate about string based on user settings.

        Automatically checks the CONCISE_DESCRIPTIONS option to determine
        which version to return.

        Returns:
            summarized_about if user has concise mode enabled, otherwise full_about
        """
        from options import OptionKey
        from options import get_option

        concise = get_option(OptionKey.CONCISE_DESCRIPTIONS, "false").lower() == "true"
        if concise:
            return self.summarized_about
        return self.full_about

    def build_preview(
        self,
        *,
        stacks: int,
        previous_stacks: int = 0,
    ) -> RewardPreviewPayload:
        return build_preview_from_effects(
            effects=self.effects,
            summary=self.get_about_str(),
            triggers=self.preview_triggers,
            stacks=max(stacks, 1),
            previous_stacks=max(previous_stacks, 0),
            target="party",
        )

    def subscribe(self, party: Party, event: str, callback: Callable[..., object]) -> Callable[..., object]:
        from autofighter.stats import BUS

        store = self._ensure_subscription_store(party)
        entries = store.setdefault(self.id, [])
        for existing_event, existing_callback, is_cleanup in entries:
            if is_cleanup:
                continue
            if existing_event == event and existing_callback is callback:
                self._ensure_cleanup_subscription(party, entries, BUS)
                return callback
        entries.append((event, callback, False))
        BUS.subscribe(event, callback)
        self._ensure_cleanup_subscription(party, entries, BUS)
        return callback

    def unsubscribe(self, party: Party, event: str, callback: Callable[..., object]) -> None:
        from autofighter.stats import BUS

        BUS.unsubscribe(event, callback)
        store = getattr(party, "_relic_bus_subscriptions", None)
        if not store:
            return
        entries = store.get(self.id)
        if not entries:
            return
        store[self.id] = [pair for pair in entries if pair[:2] != (event, callback)]
        if not store[self.id]:
            store.pop(self.id, None)

    def clear_subscriptions(self, party: Party) -> None:
        from autofighter.stats import BUS

        store = getattr(party, "_relic_bus_subscriptions", None)
        if not store:
            return
        entries = store.pop(self.id, [])
        for event, callback, _ in entries:
            BUS.unsubscribe(event, callback)

    def _reset_subscriptions(self, party: Party) -> None:
        from autofighter.stats import BUS

        store = getattr(party, "_relic_bus_subscriptions", None)
        if not store:
            return
        callbacks = store.pop(self.id, [])
        for event, callback, _ in callbacks:
            BUS.unsubscribe(event, callback)

    @staticmethod
    def _ensure_subscription_store(
        party: Party,
    ) -> dict[str, list[tuple[str, Callable[..., object], bool]]]:
        store = getattr(party, "_relic_bus_subscriptions", None)
        if store is None:
            store = {}
            setattr(party, "_relic_bus_subscriptions", store)
        return store

    def _ensure_cleanup_subscription(
        self,
        party: Party,
        entries: list[tuple[str, Callable[..., object], bool]],
        bus: object,
    ) -> None:
        if any(entry[2] for entry in entries):
            return

        def _cleanup(*_args: object, **_kwargs: object) -> None:
            self.clear_subscriptions(party)

        entries.append(("battle_end", _cleanup, True))
        bus.subscribe("battle_end", _cleanup)
