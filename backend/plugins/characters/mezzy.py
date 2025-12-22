from dataclasses import dataclass, field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES, load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Mezzy(PlayerBase):
    id = "mezzy"
    name = "Mezzy"
    full_about = "A voracious defender whose gluttonous bulwark represents the ultimate expression of 'what doesn't kill you makes you stronger.' Mezzy literally devours enemy attacks, her unique physiology converting incoming damage into raw power that fuels her own abilities. The more her opponents throw at her, the stronger she becomes—creating a terrifying feedback loop where every assault just makes her hungrier for more. Her combat style revolves around tanking massive amounts of damage while growing exponentially more dangerous, turning what should be weakening blows into a feast that only strengthens her resolve and fighting capability."
    summarized_about = "A voracious defender who devours enemy attacks and converts them into power, growing stronger with every blow."
    looks = """
    Mezzy is a catgirl whose appearance perfectly blends an endearing charm with an underlying hint of something more formidable. Her most distinctive feature is her pair of soft, expressive cat ears that sit atop her head, covered in the same reddish fur that matches her hair. These ears swivel and twitch with remarkable independence, betraying her mood and attention even when her face remains composed. They're complemented by a long, graceful tail that sways behind her, the same warm reddish color, which tends to lash with excitement during combat or curl contentedly when she's at ease.

    Her hair is a rich, reddish hue—somewhere between auburn and copper—falling in soft waves that frame her face and cascade down her shoulders. It's kept at a practical length that doesn't interfere with movement, with a few playful strands often escaping to fall across her forehead or cheeks. Her feline features give her face a delicate, heart-shaped quality with large, expressive eyes that gleam with intelligence and a mischievous spark. Her eyes shift between warm amber and green depending on the light, with vertical pupils that dilate and contract with her emotions. She has a small, button nose and a mouth that seems perpetually on the edge of a playful smile, revealing the occasional glimpse of slightly pointed canines.

    True to her nature, Mezzy is almost always seen wearing a classic maid outfit, though hers carries a distinctly personal flair. The dress is primarily black with crisp white trim—a traditional long-sleeved bodice with a white apron tied at the waist, the skirt falling to just above her knees with layers of petticoats beneath that give it a modest bounce. White frills accent the collar and cuffs, and a delicate white headpiece sits neatly atop her head, positioned carefully between her ears. The outfit is immaculately maintained, though the occasional scuff or smudge after battle hints at the rough-and-tumble nature of her work. Her hands, often gloved in white, are deft and quick, equally comfortable holding a serving tray or bracing for an incoming attack.

    Despite her cute and approachable appearance, there's a sturdiness to Mezzy's build that becomes apparent upon closer inspection. She's not frail or delicate—her frame carries a solid, grounded quality, with strong legs and capable arms that belie the decorative uniform. She moves with surprising agility for someone who specializes in taking hits, her feline grace allowing her to pivot and position herself with ease. Her posture is confident and open, shoulders back, tail swishing with self-assurance, as if daring opponents to try their best.

    In combat, Mezzy's demeanor shifts from playful to intensely focused. Her eyes narrow with concentration, pupils becoming thin slits, and her smile takes on a more predatory edge—as if she's genuinely eager to see what her opponents can throw at her. She plants herself firmly, bracing to receive attacks with a kind of hungry anticipation, her tail lashing excitedly as she feeds on the incoming damage. After absorbing a particularly powerful strike, there's a momentary shimmer around her, as if the energy is being metabolized and redistributed throughout her body, making her seem just a bit more vibrant and dangerous.

    Overall, Mezzy presents as a disarmingly cute catgirl maid whose gentle appearance masks a voracious combat style. The juxtaposition of her adorable exterior—complete with reddish fur, expressive ears, and pristine maid uniform—with her relentless, damage-devouring approach to battle makes her both memorable and surprisingly intimidating. She embodies the idea that cuteness and ferocity are not mutually exclusive, and that sometimes the most charming exterior hides the most unshakeable defender.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["mezzy_gluttonous_bulwark"])
