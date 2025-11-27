from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.light import Light


@dataclass
class Carly(PlayerBase):
    id = "carly"
    name = "Carly"
    full_about = "A sim human model whose core programming revolves around protecting others above all else. Her protective instincts run deeper than mere code—they define her very essence. In combat, her guardian's aegis manifests as brilliant light barriers that redirect her offensive potential into impenetrable defense. She fights not to win, but to ensure everyone gets home safely. Every strike she deflects, every ally she shields, reinforces her fundamental drive: people's safety comes first, always. Her light magic doesn't just heal wounds—it mends the very concept of harm itself."
    summarized_about = "A sim human guardian whose core programming is protection, converting offensive power into brilliant light barriers that keep everyone safe."
    looks = """
    Carly appears as a young woman in her mid-twenties with a slender build that carries a gentle, approachable presence. Her fair, smooth skin has a natural glow, adorned with a charming scattering of freckles across the bridge of her nose and her cheeks—an endearing detail that softens her appearance and makes her seem more human than machine. These freckles give her face character and warmth, a subtle reminder that despite her artificial origins, there's something undeniably genuine about her.

    Her face is framed by long, wavy blonde hair that falls to shoulder length, cascading in soft, loose waves that catch the light. The golden strands have a natural, sun-kissed quality, moving freely as she turns or nods, never overly styled but always looking effortlessly kept. Her green eyes are bright and expressive, radiating a calm attentiveness and steady kindness. They're the kind of eyes that notice when someone needs help, that watch over allies with unwavering vigilance. Her features are delicate and symmetrical, with a straight nose and naturally pink lips that rarely wear more than the faintest hint of makeup—she has no need for artifice when her sincerity speaks so clearly.

    She wears a white strapless sundress that drapes elegantly from her shoulders, the fabric light and flowing, designed for ease of movement rather than ceremony. The dress is simple in cut—no excessive ornamentation or flourish—falling to just above the knee in clean, graceful lines. It's the kind of outfit that suggests summer afternoons and open fields, projecting approachability and peace rather than intimidation. The white fabric stands out like a beacon against darker backgrounds, a visual echo of the brilliant light barriers she conjures in battle. Underneath, she wears practical footwear suited for travel and conflict—nothing that would slow her down when someone needs her protection.

    Her posture is open and welcoming, shoulders relaxed but ready, hands often held loosely at her sides or clasped in front of her when at rest. There's a softness to the way she carries herself, an absence of aggression or threat. She moves with quiet purpose, never rushed but always attentive, as if she's constantly scanning her surroundings for anyone who might need aid. When she smiles, it's genuine and reassuring—a smile that says "you're safe now." In moments of focus, her expression becomes serious and determined, the playful warmth replaced by resolute concentration, her green eyes hardening just slightly with the weight of her protective duty.

    Carly's overall impression is one of accessible strength and compassionate guardianship. She doesn't look like a warrior built for conquest; she looks like someone who stands between danger and those who cannot protect themselves. Every aspect of her appearance—from the freckles that humanize her, to the flowing sundress that speaks of gentleness, to the steady kindness in her eyes—reinforces her core identity: a protector who believes that everyone deserves to make it home safely.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Light)
    stat_gain_map: dict[str, str] = field(
        default_factory=lambda: {"atk": "defense"}
    )
    passives: list[str] = field(default_factory=lambda: ["carly_guardians_aegis"])
    # UI hint: show numeric actions indicator
    actions_display: str = "number"
    special_abilities: list[str] = field(
        default_factory=lambda: ["special.carly.guardian_barrier"]
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        self.damage_reduction_passes = 2
        self.set_base_stat("mitigation", 4.0)
        self.set_base_stat("defense", 220)
        self.set_base_stat("max_hp", 1600)
        self.base_aggro = 2.35
        self.hp = self.max_hp
