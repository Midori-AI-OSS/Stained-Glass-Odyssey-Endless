"""Battle event helpers for room lifecycle signals."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from autofighter.stats import BUS

__all__ = ["handle_battle_start", "handle_battle_end"]


async def handle_battle_start(
    foes: Iterable[Any],
    party_members: Iterable[Any],
    registry: Any,
) -> None:
    """Emit battle start events for all combatants."""

    foes = tuple(foes)
    members = tuple(party_members)

    for foe_obj in foes:
        await BUS.emit_async("battle_start", foe_obj)
        await registry.trigger(
            "battle_start",
            foe_obj,
            party=members,
            foes=foes,
        )

    for member in members:
        await BUS.emit_async("battle_start", member)
        await registry.trigger(
            "battle_start",
            member,
            party=members,
            foes=foes,
        )


async def handle_battle_end(
    foes: Iterable[Any],
    party_members: Iterable[Any],
) -> None:
    """Emit defeat and battle end events for combatants."""

    foes = tuple(foes)
    members = tuple(party_members)

    try:
        for foe_obj in foes:
            if getattr(foe_obj, "hp", 1) <= 0:
                await BUS.emit_async("entity_defeat", foe_obj)
        for member in members:
            if getattr(member, "hp", 1) <= 0:
                await BUS.emit_async("entity_defeat", member)
    except Exception:
        pass

    try:
        for foe_obj in foes:
            await BUS.emit_async("battle_end", foe_obj)
    except Exception:
        pass
