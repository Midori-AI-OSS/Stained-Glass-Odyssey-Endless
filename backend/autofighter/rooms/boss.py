from __future__ import annotations

from dataclasses import dataclass

from .battle.core import BattleRoom


@dataclass
class BossRoom(BattleRoom):
    """Boss rooms are tougher encounters with high scaling."""

    strength: float = 100.0
