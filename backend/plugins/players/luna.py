from dataclasses import dataclass
from dataclasses import field
from typing import Collection

from autofighter.character import CharacterType
from autofighter.mapgen import MapNode
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase
from plugins.players._base import PlayerBase


@dataclass
class Luna(PlayerBase):
    id = "luna"
    name = "Luna"
    about = "Luna Midori fights like a stargazer who mapped the constellations of violence—quiet, exact, always a beat ahead. Her thin astral halo brightens as she sketches unseen wards; the Vessel of the Twin Veils keeps station at her shoulder, flaring to tip arrows off-line. She opens by controlling the field: silvery pressure that anchors feet, a hush that snuffs a spell mid-syllable, a ripple that leaves an after-image where she stood. When steel is required, the Glimmersteel rapier writes quick, grammatical cuts, the golden quarterstaff sets the tempo and distance, and the Bladeshift dagger ends what hesitation begins. She moves light and economical—cloak skimming stone, angles over brute force—talking just enough to knock an enemy off rhythm. Her magic is moon-cold and precise: starlight darts, gravity tugs, the soft collapse of air before a controlled blast—never wasteful, always aimed at the lever that topples the fight. She isn't a brawler; she's a clockmaker in a storm, turning the right gear until the whole field ticks her way."
    ##
    char_type: CharacterType = CharacterType.B
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type("Generic")
    )
    passives: list[str] = field(default_factory=lambda: ["luna_lunar_reservoir"])
    # UI hint: show numeric actions indicator
    actions_display: str = "number"

    @classmethod
    def get_spawn_weight(
        cls,
        *,
        node: MapNode,
        party_ids: Collection[str],
        recent_ids: Collection[str] | None = None,
        boss: bool = False,
    ) -> float:
        if cls.id in {str(pid) for pid in party_ids}:
            return 0.0

        try:
            floor = int(getattr(node, "floor", 0))
        except Exception:
            floor = 0

        if boss and floor % 3 == 0:
            return 6.0
        return 1.0
