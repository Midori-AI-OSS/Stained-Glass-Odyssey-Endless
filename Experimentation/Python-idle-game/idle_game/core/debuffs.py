"""Debuff system for negative status effects.

Provides base classes and registry for debuff effects that weaken characters.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import ClassVar
from typing import Dict
from typing import Mapping
from typing import Optional

from .stat_effect import StatEffect
from .stats import Stats


@dataclass
class DebuffBase:
    """Base class for all debuff effects.

    Debuffs are negative status effects that weaken character stats temporarily
    or permanently. They use the StatEffect system for stat modifications.
    """

    plugin_type: ClassVar[str] = "debuff"

    id: str = ""
    name: str = ""
    stat_modifiers: Dict[str, float] = field(default_factory=dict)
    duration: int = -1  # -1 for permanent, >0 for temporary
    stack_display: str = "pips"
    max_stacks: Optional[int] = None

    def __post_init__(self) -> None:
        """Ensure stat modifiers use a fresh mapping per instance."""
        self.stat_modifiers = dict(self.stat_modifiers)

    def build_effect_name(
        self,
        *,
        stack_index: Optional[int] = None,
        effect_name: Optional[str] = None,
    ) -> str:
        """Build unique effect name for stacking."""
        base = effect_name or self.id or self.name or self.__class__.__name__.lower()
        if stack_index is not None:
            return f"{base}_{stack_index}"
        return base

    def build_effect(
        self,
        *,
        stack_index: Optional[int] = None,
        effect_name: Optional[str] = None,
        duration: Optional[int] = None,
        source: Optional[str] = None,
        modifiers: Optional[Mapping[str, float]] = None,
        multiplier: Optional[float] = None,
    ) -> StatEffect:
        """Build a StatEffect from this debuff's configuration."""
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

    def apply(
        self,
        target: Stats,
        *,
        stack_index: Optional[int] = None,
        effect_name: Optional[str] = None,
        duration: Optional[int] = None,
        source: Optional[str] = None,
        modifiers: Optional[Mapping[str, float]] = None,
        multiplier: Optional[float] = None,
    ) -> StatEffect:
        """Apply this debuff to a target Stats object."""
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
        """Return a human-readable description of this debuff."""
        raise NotImplementedError


class DebuffRegistry:
    """Registry for debuff effect types.

    Manages registration and application of debuff effects.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, type[DebuffBase]] = {}

    def register(self, debuff_id: str, debuff_class: type[DebuffBase]) -> None:
        """Register a debuff class by ID."""
        self._registry[debuff_id] = debuff_class

    def get_debuff(self, debuff_id: str) -> Optional[type[DebuffBase]]:
        """Get a debuff class by ID."""
        return self._registry.get(debuff_id)

    def all_debuffs(self) -> Dict[str, type[DebuffBase]]:
        """Get all registered debuff classes."""
        return dict(self._registry)

    def apply_debuff(
        self,
        debuff_id: str,
        target: Stats,
        *,
        init_kwargs: Optional[Mapping[str, object]] = None,
        **apply_kwargs: object,
    ) -> StatEffect:
        """Apply a debuff by ID to a target.

        Args:
            debuff_id: ID of the debuff to apply
            target: Target Stats object
            init_kwargs: Arguments for debuff instantiation
            **apply_kwargs: Arguments for debuff application

        Returns:
            The created StatEffect

        Raises:
            KeyError: If debuff_id is not registered
        """
        debuff_cls = self.get_debuff(debuff_id)
        if debuff_cls is None:
            raise KeyError(f"Unknown debuff '{debuff_id}'")

        init_args = dict(init_kwargs or {})
        debuff = debuff_cls(**init_args)
        return debuff.apply(target, **apply_kwargs)
