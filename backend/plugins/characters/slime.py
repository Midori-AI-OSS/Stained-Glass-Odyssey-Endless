from dataclasses import dataclass
from typing import ClassVar

from plugins.characters._base import PlayerBase


@dataclass
class Slime(PlayerBase):
    """Unobtainable training dummy that mirrors base player stats."""

    id = "slime"
    name = "Slime"
    gacha_rarity = 0
    ui_non_selectable: ClassVar[bool] = True
