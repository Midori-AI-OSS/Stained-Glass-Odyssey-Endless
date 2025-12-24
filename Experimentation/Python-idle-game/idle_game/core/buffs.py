"""Buff system for positive status effects.

Provides base classes and registry for buff effects that enhance character stats.
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
class BuffBase:
    """Base class for all buff effects.

    Buffs are positive status effects that enhance character stats temporarily
    or permanently. They use the StatEffect system for stat modifications.
    """

    plugin_type: ClassVar[str] = "buff"

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
        """Build a StatEffect from this buff's configuration."""
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
        """Apply this buff to a target Stats object."""
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
        """Return a human-readable description of this buff."""
        raise NotImplementedError


class BuffRegistry:
    """Registry for buff effect types.

    Manages registration and application of buff effects.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, type[BuffBase]] = {}

    def register(self, buff_id: str, buff_class: type[BuffBase]) -> None:
        """Register a buff class by ID."""
        self._registry[buff_id] = buff_class

    def get_buff(self, buff_id: str) -> Optional[type[BuffBase]]:
        """Get a buff class by ID."""
        return self._registry.get(buff_id)

    def all_buffs(self) -> Dict[str, type[BuffBase]]:
        """Get all registered buff classes."""
        return dict(self._registry)

    def apply_buff(
        self,
        buff_id: str,
        target: Stats,
        *,
        init_kwargs: Optional[Mapping[str, object]] = None,
        **apply_kwargs: object,
    ) -> StatEffect:
        """Apply a buff by ID to a target.

        Args:
            buff_id: ID of the buff to apply
            target: Target Stats object
            init_kwargs: Arguments for buff instantiation
            **apply_kwargs: Arguments for buff application

        Returns:
            The created StatEffect

        Raises:
            KeyError: If buff_id is not registered
        """
        buff_cls = self.get_buff(buff_id)
        if buff_cls is None:
            raise KeyError(f"Unknown buff '{buff_id}'")

        init_args = dict(init_kwargs or {})
        buff = buff_cls(**init_args)
        return buff.apply(target, **apply_kwargs)
