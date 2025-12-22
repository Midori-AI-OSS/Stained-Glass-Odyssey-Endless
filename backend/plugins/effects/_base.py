from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Mapping

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class StatEffectPlugin:
    """Base helper for buffs and debuffs backed by StatEffect."""

    plugin_type: ClassVar[str] = ""
    id: str = ""
    name: str = ""
    stat_modifiers: dict[str, float] = field(default_factory=dict)
    duration: int = -1
    stack_display: str = "pips"
    max_stacks: int | None = None

    def __post_init__(self) -> None:
        # Ensure stat modifiers always use a fresh mapping per instance.
        self.stat_modifiers = dict(self.stat_modifiers)

    def build_effect_name(
        self,
        *,
        stack_index: int | None = None,
        effect_name: str | None = None,
    ) -> str:
        base = effect_name or self.id or self.name or self.__class__.__name__.lower()
        if stack_index is not None:
            return f"{base}_{stack_index}"
        return base

    def build_effect(
        self,
        *,
        stack_index: int | None = None,
        effect_name: str | None = None,
        duration: int | None = None,
        source: str | None = None,
        modifiers: Mapping[str, float] | None = None,
        multiplier: float | None = None,
    ) -> StatEffect:
        values = dict(self.stat_modifiers)
        if modifiers:
            for key, value in modifiers.items():
                values[key] = value
        if multiplier is not None:
            values = {key: val * multiplier for key, val in values.items()}
        resolved_duration = self.duration if duration is None else duration
        effect_source = source or (self.id or self.name or self.__class__.__name__.lower())
        return StatEffect(
            name=self.build_effect_name(stack_index=stack_index, effect_name=effect_name),
            stat_modifiers=values,
            duration=resolved_duration,
            source=effect_source,
        )

    async def apply(
        self,
        target: "Stats",
        *,
        stack_index: int | None = None,
        effect_name: str | None = None,
        duration: int | None = None,
        source: str | None = None,
        modifiers: Mapping[str, float] | None = None,
        multiplier: float | None = None,
    ) -> StatEffect:
        effect = self.build_effect(
            stack_index=stack_index,
            effect_name=effect_name,
            duration=duration,
            source=source,
            modifiers=modifiers,
            multiplier=multiplier,
        )
        target.add_effect(effect)
        return effect

    @classmethod
    def get_description(cls) -> str:
        raise NotImplementedError


@dataclass
class BuffBase(StatEffectPlugin):
    plugin_type: ClassVar[str] = "buff"


@dataclass
class DebuffBase(StatEffectPlugin):
    plugin_type: ClassVar[str] = "debuff"
