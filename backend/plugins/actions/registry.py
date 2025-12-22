"""Registry for tracking action plugins and cooldown state."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Sequence

from ._base import ActionType

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from autofighter.stats import Stats

    from ._base import ActionBase, ActionType


class ActionRegistry:
    """Central registry used by the battle turn loop."""

    def __init__(self) -> None:
        self._actions: dict[str, type[ActionBase]] = {}
        self._actions_by_type: dict[str, list[str]] = defaultdict(list)
        self._character_actions: dict[str, list[str]] = {}
        self._cooldowns: dict[str, dict[str, int]] = defaultdict(dict)
        self._ultimate_actions: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Registration helpers
    def register_action(self, action_class: type[ActionBase]) -> None:
        """Register a plugin class that declares ``plugin_type = 'action'``."""

        if getattr(action_class, "plugin_type", None) != "action":
            raise ValueError(f"{action_class} is not an action plugin")

        # Instantiate to get the actual ID value from the dataclass
        try:
            instance = action_class()
            action_id = instance.id
        except Exception as e:
            raise ValueError(f"Failed to instantiate {action_class} to read id: {e}") from e

        if not action_id:
            raise ValueError("Action plugins must declare a stable id")
        if action_id in self._actions:
            raise ValueError(f"Duplicate action id detected: {action_id}")
        self._actions[action_id] = action_class

        # Get action type from instance
        action_type = str(instance.action_type)
        self._actions_by_type.setdefault(action_type, []).append(action_id)

        damage_type_id = getattr(instance, "damage_type_id", None)
        if (
            action_type == str(ActionType.ULTIMATE)
            and isinstance(damage_type_id, str)
            and damage_type_id
        ):
            key = self._normalize_damage_type_id(damage_type_id)
            self._ultimate_actions[key] = action_id

    def register_character_actions(
        self,
        character_id: str,
        action_ids: Sequence[str],
    ) -> None:
        """Assign a loadout to a combatant identified by ``character_id``."""

        self._character_actions[character_id] = list(dict.fromkeys(action_ids))

    # ------------------------------------------------------------------
    # Lookup helpers
    def instantiate(self, action_id: str) -> ActionBase:
        """Return a new action instance for *action_id*."""

        action_class = self._actions.get(action_id)
        if action_class is None:
            raise KeyError(f"Unknown action id: {action_id}")
        return action_class()

    def get_action_class(self, action_id: str) -> type[ActionBase]:
        action = self._actions.get(action_id)
        if action is None:
            raise KeyError(f"Unknown action id: {action_id}")
        return action

    def get_actions_by_type(self, action_type: ActionType | str) -> list[type[ActionBase]]:
        """Return all action classes for a given ``ActionType``."""

        key = str(action_type)
        return [self._actions[action_id] for action_id in self._actions_by_type.get(key, [])]

    def instantiate_ultimate(self, damage_type_id: str) -> ActionBase | None:
        """Return an ultimate action instance for the provided damage type."""

        action_id = self._ultimate_actions.get(self._normalize_damage_type_id(damage_type_id))
        if not action_id:
            return None
        try:
            return self.instantiate(action_id)
        except KeyError:
            return None

    def get_character_actions(self, character_id: str) -> list[type[ActionBase]]:
        """Return the action classes associated with *character_id*."""

        action_ids = self._character_actions.get(character_id, [])
        return [self._actions[action_id] for action_id in action_ids if action_id in self._actions]

    # ------------------------------------------------------------------
    # Cooldown helpers
    def is_available(self, actor: "Stats", action: ActionBase) -> bool:
        actor_id = self._actor_key(actor)
        cooldowns = self._cooldowns.get(actor_id, {})
        return cooldowns.get(action.id, 0) <= 0

    def start_cooldown(self, actor: "Stats", action: ActionBase) -> None:
        actor_id = self._actor_key(actor)
        turns = max(int(getattr(action, "cooldown_turns", 0)), 0)
        if turns <= 0:
            return
        tags = {tag for tag in getattr(action, "tags", ()) if tag}
        target_ids: set[str] = {action.id}
        if tags:
            for candidate_id, candidate_class in self._actions.items():
                # Instantiate to get tags from the dataclass
                try:
                    candidate_instance = candidate_class()
                    candidate_tags = set(getattr(candidate_instance, "tags", ()))
                    if tags & candidate_tags:
                        target_ids.add(candidate_id)
                except Exception:
                    # Skip actions that can't be instantiated
                    continue
        actor_cooldowns = self._cooldowns.setdefault(actor_id, {})
        for target in target_ids:
            actor_cooldowns[target] = max(turns, actor_cooldowns.get(target, 0))

    def advance_cooldowns(self) -> None:
        """Tick down every active cooldown by one turn."""

        for actor_id, cooldowns in list(self._cooldowns.items()):
            expired = []
            for action_id, turns in list(cooldowns.items()):
                if turns <= 1:
                    expired.append(action_id)
                else:
                    cooldowns[action_id] = turns - 1
            for action_id in expired:
                cooldowns.pop(action_id, None)
            if not cooldowns:
                self._cooldowns.pop(actor_id, None)

    def reset_actor(self, actor: "Stats") -> None:
        """Remove cooldown tracking for *actor* (e.g., when they die)."""

        self._cooldowns.pop(self._actor_key(actor), None)

    # ------------------------------------------------------------------
    @staticmethod
    def _actor_key(actor: "Stats") -> str:
        return str(getattr(actor, "id", id(actor)))

    @staticmethod
    def _normalize_damage_type_id(damage_type_id: str | None) -> str:
        if not damage_type_id:
            return "generic"
        return str(damage_type_id).strip().lower() or "generic"
