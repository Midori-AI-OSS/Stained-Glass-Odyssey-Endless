from dataclasses import dataclass, field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES, load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Graygray(PlayerBase):
    id = "graygray"
    name = "Graygray"
    full_about = "A tactical mastermind whose counter maestro abilities transform every enemy attack into a lesson in superior combat technique. Graygray doesn't just defend—she conducts battles like a symphony, turning opponent aggression into the very notes of their defeat. Her strategic brilliance lies in reading attack patterns and responding with perfectly timed counters that not only negate damage but convert that energy into devastating retaliations. Each strike against her becomes a teaching moment, as she demonstrates how true mastery lies not in overwhelming force, but in precise timing and flawless technique."
    summarized_about = "A tactical mastermind who conducts battles like a symphony, converting enemy attacks into perfectly timed counters."
    looks = """
A compact, athletic build with an approachable, practical presence. Her face is open and expressive—warm eyes that watch for patterns and a ready, rueful smile that suggests quiet confidence more than bravado. Her complexion is natural and unadorned; she favors a utilitarian, lived-in look over anything ornate.

;Hair falls to short/medium length, often tousled and casually swept to one side; the color reads as a soft, ashy blonde with darker roots. Her everyday wardrobe skews comfortable and functional: worn hoodies, simple tees, and relaxed jeans in muted tones (grays, faded blues, soft creams). A well-loved sweatshirt or hoodie is a common layer, the kind that looks like it has been lived in.

Small, informal accessories complete her silhouette—over-ear headphones often hang around her neck, and she sometimes wears a practical band or bracelet. Her posture is relaxed and thoughtful; she often sits with arms or legs crossed when mulling over a tactic, and she leans in when engaged, curious and attentive rather than theatrical.

Subtle, thematic visual effects accompany her focus: when she syncs to an opponent's rhythm or prepares a counter, faint silver-gray motes or musical-note-like glyphs gather briefly around her hands and shoulders. These are understated—an echo of tempo and timing rather than full spectacle—and they fade as quickly as they appear.
"""
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["graygray_counter_maestro"])
    special_abilities: list[str] = field(
        default_factory=lambda: ["special.graygray.counter_opus"]
    )
