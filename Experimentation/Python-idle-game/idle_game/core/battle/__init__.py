"""Battle system components for combat resolution.

This package contains the core battle engine ported from backend for Qt-based gameplay.
"""

from .engine import BattleResult
from .engine import run_battle
from .initialization import TurnLoopContext
from .initialization import initialize_turn_loop

__all__ = [
    "BattleResult",
    "run_battle",
    "TurnLoopContext",
    "initialize_turn_loop",
]
