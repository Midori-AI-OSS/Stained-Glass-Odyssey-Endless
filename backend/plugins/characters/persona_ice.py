from dataclasses import dataclass, field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.ice import Ice


@dataclass
class PersonaIce(PlayerBase):
    id = "persona_ice"
    name = "PersonaIce"
    full_about = (
        "A disciplined cryokinetic tank who keeps his real name hidden behind the Persona"
        "Ice moniker. He is most comfortable blanketing a battlefield in calming frost, "
        "projecting the chill aura that never leaves his ice-blue hair. PersonaIce fights "
        "to shield his sisters—Lady of Fire and Lady Fire and Ice—layering protective cold "
        "around them before reshaping it into restorative mist. Though still barely past "
        "his twentieth winter, the human wanderer has mastered a meditative cycle of ice "
        "that hardens against enemy blows and then thaws into healing for the party."
    )
    summarized_about = "A disciplined cryokinetic tank who shields his sisters with protective frost that hardens against blows and heals allies."
    looks = """
    Persona Ice is a young man who appears to be around eighteen years old, though his mastery of cryokinetic abilities suggests a maturity beyond his years. He presents as someone who has chosen simplicity and function over ostentation, his entire appearance reflecting the calm, meditative discipline that defines his combat philosophy.

    His most distinctive feature is his light blue hair—not the pale, almost white shade of frost, but a clear, cool blue like shallow water over ice, or the heart of a glacier catching sunlight. The color is striking and unmistakable, permanently tinted by the constant flow of cryokinetic energy through his system. The hair is kept at a practical, medium length, styled simply without elaborate arrangement—falling naturally with perhaps a slight tousle, as if wind-blown or casually run through with his fingers. It frames his face in soft, unstructured layers, occasionally falling across his forehead or into his eyes, requiring the occasional brush-aside with his hand. The blue strands seem to carry a faint chill, as if touching them might feel like running your fingers through snow.

    His face is youthful and open, with gentle features that haven't yet fully hardened into the angular planes of full adulthood. He has clear, fair skin with a cool undertone—pale but healthy, as if he spends time outdoors in cold climates rather than hiding from the sun. His eyes, while not extensively described in the task, would logically complement his ice affinity and light blue hair—perhaps a lighter shade of blue or even pale gray, carrying the calm, steady gaze of someone who has learned to center himself in the midst of chaos. His expression tends toward quiet composure, a neutral set to his features that can shift to intense focus during combat or warm affection when his sisters are near.

    Persona Ice favors extremely practical attire: a light blue t-shirt and shorts that prioritize mobility and comfort over protection or formality. The t-shirt is simple and well-fitted, the same cool blue as his hair, made of breathable fabric that moves with him easily. The shorts are similarly practical—likely hitting just above the knee, allowing complete freedom of movement for someone who needs to pivot, plant, and reposition constantly in his role as a defensive anchor. This casual outfit might seem inadequate for a battlefield, but it speaks to his confidence in his abilities—he doesn't need heavy armor when he can create barriers of ice, and restrictive clothing would only hinder the fluid movements required for his meditative combat style.

    Despite the casual nature of his clothing, there's nothing sloppy about his appearance. Everything is clean and well-maintained, suggesting someone who values order and discipline even in small things. He moves with an economy of motion that speaks to trained efficiency—no wasted steps, no unnecessary flourishes. When he walks, it's with a centered balance, weight evenly distributed, always ready to shift into a defensive stance. His posture is upright but not rigid, relaxed but attentive, embodying the calm-alert state of someone who has mastered the art of being present without being tense.

    In combat or when channeling his powers, there's a visible manifestation of his cryokinetic abilities. A subtle mist often forms around him, tendrils of cold vapor rising from his skin like morning fog over frozen ground. Frost might crystallize on his forearms or shoulders, creating intricate patterns of ice that melt away when he releases the energy into protective barriers or healing mist. The air around him carries a noticeable chill—not uncomfortable, but distinct, like stepping into the shade on a winter day or opening a freezer door. When he's deeply focused on maintaining his defensive cycle, small snowflakes might form and drift in the air around him, melting before they hit the ground.

    There's a protective quality to his bearing when his sisters are present—a subtle shift in his stance, positioning himself slightly forward or to the side, creating space for them to operate while maintaining awareness of their positions. He doesn't hover or crowd, but there's no doubt that his primary concern is their safety. The meditative calm he projects serves dual purposes: it centers his own abilities, allowing precise control over his ice, but it also provides a stabilizing presence for those around him, a steady anchor in the chaos of battle.

    Overall, Persona Ice presents as a young, unassuming figure whose light blue hair immediately marks him as something more than ordinary. His simple clothing and calm demeanor create an approachable, almost humble impression, but there's an underlying strength and purpose in every aspect of his bearing. He is the ice that shields, the frost that soothes, the winter guardian who asks for no recognition beyond knowing that those he protects are safe. In a world of flashy combat styles and elaborate armor, he stands out precisely because he doesn't try to—his power speaks through his actions, his identity hidden behind a moniker, his true self revealed only through the unwavering dedication with which he defends those he loves.
    """
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Ice)
    passives: list[str] = field(default_factory=lambda: ["persona_ice_cryo_cycle"])

    def __post_init__(self) -> None:
        super().__post_init__()
        self.damage_reduction_passes = 2
        self.set_base_stat("mitigation", 4.0)
        self.set_base_stat("defense", 210)
        self.set_base_stat("max_hp", 1650)
        self.base_aggro = 2.35
        self.hp = self.max_hp
