from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class PersonaLightAndDark(PlayerBase):
    id = "persona_light_and_dark"
    name = "PersonaLightAndDark"
    full_about = (
        "A 6★ guardian and brother to Lady Light and Lady Darkness, Persona Light and Dark fights to keep "
        "his sisters safe. He speaks only the radiant glyphs of the Light tongue, letting sweeping gestures "
        "and twin halos translate his intent. By trading between the family's luminous ward and shadow bastion, "
        "he drags enemy focus onto himself while sheltering the people he protects."
    )
    summarized_about = "A guardian brother who trades between light and shadow, drawing enemy focus to protect his sisters and allies."
    looks = """
    Persona Light and Dark stands at an imposing 6′2″ with the broad-shouldered, protective build of a born guardian. Despite appearing ageless, his face suggests someone in their early to mid-twenties, approximately the same age as his sisters Lady Light and Lady Darkness, around twenty-three years old. His features are strong and symmetrical—a square jawline, straight nose, and expressive eyes that shift between luminous gold and deep shadow depending on which aspect of his dual nature is dominant. His physique is that of someone built for endurance and protection: well-muscled but not bulky, with the kind of balanced strength that allows him to position himself between danger and those he shields.
    His most extraordinary feature is his hair: a natural salt-and-pepper blend of pure white and jet black strands woven together in equal measure. The pattern isn't a simple mix but rather an intricate interweaving, creating a striking visual harmony that mirrors his dual nature. Throughout the black and white locks, tiny sparkles catch the light—the same starlike flecks that shimmer in his sisters' hair, a family signature that marks all three as bound by more than just blood. The effect is mesmerizing: in bright light, the white strands glow while black ones absorb shadow; in darkness, the sparkles emerge like captured starlight. He keeps his hair medium length, falling to just above his shoulders, where it naturally frames his face and emphasizes the symmetry of his dual alignment.
    Two radiant halos hover above his crown, one slightly higher than the other, creating a double-ringed aureole that serves as his most constant identifier. The halos are not theatrical—they sit there as facts of his existence, thin circlets of pure energy. The upper halo glows with pale golden-white light, while the lower one pulses with deep purple-black luminescence, the two rings rotating slowly in opposite directions like celestial gears. When he draws upon his light aspect, both halos brighten and align; when shadow is needed, they dim and desynchronize. The halos act as emotional indicators as well, flaring protectively when his sisters or allies are threatened, or softening to a gentle pulse during moments of peace.
    His attire reflects his role as guardian and his connection to the duality of existence. He favors a form-fitting combat suit in layered blacks and whites that echo his hair—asymmetric panels of obsidian and pearl that create a visual language of balance without symmetry. Over this, he wears a flowing half-cape that drapes from his right shoulder, the fabric shifting from white at the top to black at the hem, or vice versa depending on light and angle. Heavy boots anchor him to the ground, reinforced at shin and thigh with articulated guards that bear his family's sigil. His hands are usually bare or wrapped in minimal fabric, allowing him to trace the radiant glyphs of the Light tongue—the only language he speaks—through sweeping gestures that hang in the air as luminous calligraphy before dissipating into motes of light or shadow.
    When magic flows through him, the transformation is dramatic. Light manifestations cause his skin to emit a soft, warm radiance, the halos spinning faster and aligning into perfect concentric circles that project protective barriers around his allies. Shadow aspects darken his presence, causing the air around him to dim as if he's absorbing ambient light, the lower halo expanding into a basin of protective darkness that obscures and confuses enemies. The transitions between states are smooth and practiced—one moment he's a beacon drawing all attention, the next he's a void that enemies can't help but fixate upon, all while his sisters and allies operate safely in the space he creates.
    His bearing is that of unwavering protection. He stands square and grounded, weight distributed evenly, always positioning himself between threats and those he guards. His gestures are large and deliberate, each movement painting glyphs that communicate complex ideas to those who understand—warnings, reassurances, tactical signals. Though he speaks no conventional words, his intent is never unclear: his eyes hold steady contact, his stance broadcasts dedication, and the twin halos pulse in rhythms that his sisters have learned to read as clearly as speech. In combat he moves with controlled aggression, drawing strikes toward himself through sheer presence, while in quiet moments he maintains a watchful stillness, the salt-and-pepper sparkle of his hair catching firelight as he keeps vigil over those entrusted to his care.
    """
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(["Light", "Dark"]))
    )
    passives: list[str] = field(
        default_factory=lambda: ["persona_light_and_dark_duality"]
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        self.damage_reduction_passes = 2
        self.set_base_stat("mitigation", 4.0)
        self.set_base_stat("defense", 240)
        self.set_base_stat("max_hp", 1700)
        self.base_aggro = 2.35
        self.hp = self.max_hp
