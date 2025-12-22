from dataclasses import dataclass, field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Ryne(PlayerBase):
    id = "ryne"
    name = "Ryne"
    full_about = (
        "Ryne Waters is a 6★ Oracle of Light who chose her own name and future after escaping"
        " Eulmore. She now leads restoration missions across the Empty with calm resolve,"
        " balancing empathy with a scout's edge learned alongside her mentor Thancred."
        " Her partnership with Luna Midori keeps both grounded—Luna tempers Ryne's habit of"
        " carrying every burden alone while Ryne helps Luna open up to the communities they"
        " protect. In battle she channels light through twin blades or a borrowed gunblade,"
        " moving with agile precision to cleanse aetheric storms and shield her friends."
    )
    summarized_about = "An Oracle of Light who leads restoration missions with calm resolve, channeling light through twin blades with agile precision."
    looks = """
    Ryne (Oracle of Light)
    SUBJECT — FACE & HEAD
    - Age appearance: **teenage**; soft, youthful features; gentle roundness to cheeks; subtle pointed chin; straight, delicate nose; natural pink lips.
    - Eyes: **pale blue**, luminous, alert; medium-length lashes; calm, determined gaze; eyebrows soft and slightly arched.
    - Expression: composed, kind, quietly resolute; a hint of cautious optimism at the corners of the mouth.

    HAIR
    - Color: **vivid red** (natural, warm-toned).
    - Length & shape: very long, flowing past the shoulder blades; soft layers framing the face; silky texture with a light, natural sheen.
    - Styling details: neat crown; a **small accent braid** on one side; a few wisps escaping near the temples for movement.

    BODY & PROPORTION
    - Build: **petite, athletic**; balanced proportions; graceful posture indicating agility and training.
    - Skin: fair, smooth complexion with a healthy, natural glow; no heavy makeup.

    COSTUME — ORACLE OF LIGHT ATTIRE (character-accurate)
    - Primary garment: elegant **white one-piece dress** tailored for mobility; **V-neckline**; **off-shoulder** design; **puffed sleeves** that taper neatly at the forearm; subtle ribbon lacing and tasteful decorative cutwork on the bodice.
    - Silhouette: fitted through the waist with light, flowing fabric that allows clear leg movement; tasteful, practical design (no exaggerated frills).
    - Legs: white leggings/pantalettes consistent with the outfit’s design.
    - Footwear: **white knee-high boots**, practical adventurer style; clean lines and secure fastenings; comfortable but sturdy profile.
    - Accessories (subtle): minimal jewelry; small, functional fasteners and seams; overall aesthetic is serene and **light-aspected** without ornate armor plating.

    WEAPONS (IF HANDHELD — for action poses only; do not invent extra gear)
    - **Twin daggers** associated with her role (short, elegant blades with crystalline/light motifs); compact guards; balanced for swift strikes.

    TEXTURE & MATERIAL DIRECTIONS
    - Fabric reads as lightweight and breathable, with subtle stitching and ribbon details visible upon close inspection.
    - Leather of boots appears supple yet firm; edges and seams clearly defined.
    - Metal of dagger hilts has a muted, brushed finish; blades are clean, sharp, and reflective without excessive glare.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(default_factory=lambda: load_damage_type("Light"))
    passives: list[str] = field(default_factory=lambda: ["ryne_oracle_of_balance"])
    actions_display: str = "number"
