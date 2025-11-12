from dataclasses import dataclass
from typing import ClassVar

from plugins.characters._base import PlayerBase


@dataclass
class Slime(PlayerBase):
    """Unobtainable training dummy that mirrors base player stats."""

    id = "slime"
    name = "Slime"
    full_about = "A basic training dummy that serves as a practice target, perfectly mirroring fundamental combat parameters without special abilities."
    summarized_about = "A basic training dummy for practice and testing."
    gacha_rarity = 0
    ui_non_selectable: ClassVar[bool] = True
