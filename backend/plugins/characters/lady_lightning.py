from dataclasses import dataclass, field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.lightning import Lightning


@dataclass
class LadyLightning(PlayerBase):
    id = "lady_lightning"
    name = "LadyLightning"
    full_about = (
        "An aasimar who answers to Electra—the storm-tossed twin of Lady Wind. "
        "Though she looks about thirty, her sunburst hair is permanently "
        "overcharged and her bright yellow eyes never stop darting. Electra broke "
        "out of the lab that laced her nerves with conductive implants, and the "
        "ordeal left her with disorganized thoughts, paranoia about whoever was "
        "pulling the switches, and manic surges that collapse into exhaustion. She "
        "insists she can hear every current humming around her, cobbling together "
        "unstable inventions or weaponizing the sparks when cornered. Even while "
        "certain the authorities are still hunting her, she fights beside the few "
        "people who believe her, channeling lightning like a prophet who cannot "
        "tell divine guidance from delusion."
    )
    summarized_about = "Lady Wind's storm-tossed twin who escaped a lab and now channels lightning with manic intensity, unable to distinguish guidance from delusion."
    looks = """
    Lady Lightning—or Electra, as she insists on being called—is a woman in her apparent thirties whose entire presence crackles with barely contained electrical energy. Her most striking feature is her hair, an extraordinary dark yellow color that seems to defy natural physics. It's not merely blonde; it's the color of raw lightning, a deep golden-yellow that appears almost incandescent in certain lights. The hair falls in wild, untamed strands that seem perpetually windswept, as if an invisible storm is constantly blowing around her. Loose bangs sweep across her forehead, sometimes obscuring one eye, sometimes swept aside by an unseen current. The entire mass has a faintly shimmering quality, as if each strand is charged with static electricity waiting to discharge.

    Her eyes are striking yellow—not the warm amber of sunlight, but the sharp, electric yellow of a lightning bolt frozen in time. They're restless, constantly darting and scanning, never settling on one point for long. There's an intensity in that gaze, a mix of hyper-vigilance and genuine terror, as if she's perpetually watching for threats that others cannot see. Her pupils are slightly dilated, giving her a wide-eyed, manic appearance that shifts between fierce determination and haunted paranoia. The skin around her eyes shows faint signs of exhaustion—dark circles that speak to sleepless nights and the toll of constant alertness—yet the eyes themselves burn with unrelenting energy.

    Her face is angular and expressive, with high cheekbones and a straight nose. She keeps her mouth closed most of the time, lips pressed into a thin line as if holding back a torrent of words or warnings. When she does speak, her expression flickers rapidly between conviction and doubt, confidence and fear. There's a weathered quality to her features despite her relative youth, the kind of worn look that comes from prolonged stress and trauma rather than age. Her skin is fair but carries a faint, almost imperceptible luminescence, the celestial heritage of her aasimar bloodline showing through despite everything she's endured.

    Electra wears a yellow off-shoulder strapless dress that seems both elegant and slightly impractical for someone living on the run. The dress is a bold, vibrant yellow—the color of warning signs and electrical hazards—falling in flowing fabric that moves with her restless energy. The off-shoulder design leaves her arms and shoulders bare, revealing skin that occasionally sparks with tiny, harmless arcs of electricity when she's particularly agitated. The dress has a shimmering quality, as if woven with metallic threads that catch and reflect light in unpredictable patterns, creating an almost strobe-like effect when she moves quickly. The garment is slightly travel-worn, with small repairs and scorch marks near the hem that tell stories of narrow escapes and improvised defenses.

    Her posture is perpetually mobile—she's always in motion, walking with quick, purposeful strides, or shifting her weight from foot to foot when forced to stand still. She moves like someone who expects danger from any direction, her gaze sweeping the environment in constant surveillance patterns. Her hands are rarely still, fingers twitching or tracing invisible circuits in the air as if conducting an orchestra only she can hear. When she gestures, small sparks sometimes leap between her fingertips, visual evidence of the electrical charge she carries within her.

    The overall impression Lady Lightning creates is one of breathtaking but unstable power. The shimmering effect that surrounds her—part divine aura, part electrical discharge—gives her an almost otherworldly appearance, as if she exists partially in this world and partially in some electric dreamscape. There's a slightly crazed edge to her expression, a wild intensity in her eyes that warns of unpredictability and danger. The dramatic lighting that seems to follow her is both literal—she generates her own ambient glow—and metaphorical, as every scene she enters becomes charged with tension and possibility.

    Electra is a figure of tragic beauty: a storm given human form, divine heritage corrupted by mortal cruelty, a prophet whose visions might be insights or delusions. The contrast between her elegant yellow dress and her wild, electric hair, between her celestial aura and her haunted eyes, creates a visual paradox that perfectly captures her fractured state—a being of light and power who has been pushed to the edge of sanity, channeling forces that could either save her allies or consume her entirely.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Lightning)
    passives: list[str] = field(default_factory=lambda: ["lady_lightning_stormsurge"])
