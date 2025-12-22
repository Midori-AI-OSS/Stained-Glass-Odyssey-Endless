from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Ixia(PlayerBase):
    id = "ixia"
    name = "Ixia"
    full_about = "A diminutive but fierce male lightning-wielder whose compact frame channels tremendous electrical energy. Despite his small stature, Ixia's tiny titan abilities allow him to unleash devastating electrical attacks that surge far beyond what his size would suggest. His lightning mastery makes him a formidable Type A combatant who proves that power isn't measured by physical dimensions but by the storm within."
    summarized_about = "A diminutive lightning-wielder who channels tremendous electrical power, proving that strength isn't measured by size."
    looks = """
    Ixia is a petite lalafel mage with a delicate, childlike silhouette—short in stature but perfectly proportioned, giving her a nimble, sprightly presence. Her skin is pale and smooth, with a subtle, healthy sheen that catches light in soft highlights. She carries herself with an easy, purposeful gait that blends curiosity and quiet confidence.

    Her face is small and finely featured: a gently rounded jaw, a small nose, and high, gently arched brows. Large, expressive eyes glow a deep, crystalline red—bright and alert, hinting at constant arcane awareness. Her ears are long and tapered to a sharp point, unmistakably lalafel and often framed by her hair.

    She wears a sleek bob cut that falls to chin length, dyed a deep midnight-blue that appears almost black in shadow but flashes navy in sunlight. Her bangs are cut straight across the forehead, with subtle inward curls that soften the face. Stray wisps and a few shorter layers around the ears give the style a natural, slightly windswept look.

    Ixia's outfit blends practical adventurer's tailoring with arcane ornamentation. She favors a fitted, sleeveless bodice of layered leather and cloth in rich violet and onyx tones, trimmed with silver filigree and geometric motifs. A ruffled white chemise peeks from under the collar and sleeves, adding a touch of contrast and old-world charm. Her skirt is short and tiered—dark pleats beneath purple panels embossed with subtle runes—allowing freedom of movement while retaining a refined silhouette.

    Her boots are knee-high, black leather with small engraved metal plates at the cuffs and practical straps; they look built to last yet are light enough for quick steps and leaps. A decorative belt with interlocking silver clasps cinches the waist and supports small satchels and trinkets—components for her craft.

    The most striking accessory is her staff: a slender, dark shaft topped with a multifaceted crystal that pulses between magenta and violet. The staff's metalwork is ornate and slightly gothic—twisting vines and crescent motifs that echo the silver patterns on her clothing. When she channels magic, faint motes of purple and pale blue light orbit the crystal and her hands, and thin threads of energy trail from her fingertips.

    Her posture is compact and poised—ready to dart or unleash a spell at a moment's notice. Mannerisms are minimal but expressive: a brief, contemplative tilt of the head when considering a new idea, a quick, precise adjustment of her staff before casting, and joyful, sudden bursts of speed when excited. Visual magical effects around her favor crystalline shards, soft luminescent motes, and cold, starlike flares that match the violet-pink glow of her staff.

    Overall, Ixia presents as a refined, small-statured lalafel spellcaster—equal parts determined apprentice and precise arcane practitioner—whose dark-violet, silver-accented wardrobe and radiant crystal staff make her presence unmistakable on any battlefield or moonlit glade.
    """
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type("Lightning")
    )
    passives: list[str] = field(default_factory=lambda: ["ixia_tiny_titan"])
    special_abilities: list[str] = field(
        default_factory=lambda: ["special.ixia.lightning_burst"]
    )
