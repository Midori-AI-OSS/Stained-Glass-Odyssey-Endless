"""Base classes for character-specific special ability actions."""

from __future__ import annotations

from dataclasses import dataclass

from plugins.actions._base import ActionBase, ActionType


@dataclass(kw_only=True, slots=True)
class SpecialAbilityBase(ActionBase):
    """Shared helpers for character-specific special abilities."""

    action_type: ActionType = ActionType.SPECIAL
    character_id: str = ""

    async def can_execute(self, actor, targets, context):
        """Validate that the correct character is using this ability."""

        if self.character_id:
            actor_id = str(getattr(actor, "id", ""))
            if actor_id != self.character_id:
                return False
        return await super().can_execute(actor, targets, context)
