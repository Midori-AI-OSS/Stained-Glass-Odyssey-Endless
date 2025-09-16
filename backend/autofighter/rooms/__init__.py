from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..mapgen import MapNode
from ..party import Party


@dataclass
class Room:
    """Base room type. Subclasses implement :meth:`resolve`."""

    node: MapNode

    async def resolve(self, party: Party, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


from .battle.core import ENRAGE_TURNS_BOSS  # noqa: E402
from .battle.core import ENRAGE_TURNS_NORMAL  # noqa: E402
from .battle.core import BattleRoom  # noqa: E402
from .boss import BossRoom  # noqa: E402
from .chat import ChatRoom  # noqa: E402
from .shop import ShopRoom  # noqa: E402
from .utils import _build_foes  # noqa: E402
from .utils import _choose_foe  # noqa: E402
from .utils import _scale_stats  # noqa: E402
from .utils import _serialize  # noqa: E402

__all__ = [
    'BattleRoom',
    'ENRAGE_TURNS_NORMAL',
    'ENRAGE_TURNS_BOSS',
    'BossRoom',
    'ChatRoom',
    'Room',
    'ShopRoom',
    '_build_foes',
    '_choose_foe',
    '_scale_stats',
    '_serialize',
]
