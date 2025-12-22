"""Result objects returned by action plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - type checking only
    pass


@dataclass(slots=True)
class AnimationTrigger:
    """Describe an animation that the pacing system should play."""

    name: str
    duration: float = 0.0
    per_target: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionResult:
    """Structured payload returned by :class:`plugins.actions.ActionBase`."""

    success: bool
    damage_dealt: dict[str, int] = field(default_factory=dict)
    healing_done: dict[str, int] = field(default_factory=dict)
    shields_added: dict[str, int] = field(default_factory=dict)
    effects_applied: list[tuple[str, str]] = field(default_factory=list)
    effects_removed: list[tuple[str, str]] = field(default_factory=list)
    resources_consumed: dict[str, int] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    animations: list[AnimationTrigger] = field(default_factory=list)
    extra_turns_granted: list[str] = field(default_factory=list)
    summons_created: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
