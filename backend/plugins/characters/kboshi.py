from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Kboshi(PlayerBase):
    id = "kboshi"
    name = "Kboshi"
    full_about = "A master of dark energy whose deep understanding of shadow and void allows him to harness forces that most fear to touch. His flux cycle abilities create devastating cyclical attacks by channeling dark energy through perpetual loops of creation and destruction. Kboshi manipulates the fundamental forces of entropy, drawing power from the spaces between light and using that darkness to fuel increasingly powerful dark magic. His energy manipulation doesn't just deal damage—it tears at the fabric of reality itself, creating vortexes of pure void that consume everything in their path before cycling back to fuel his next devastating assault."
    summarized_about = "A master of dark energy who channels void forces through cyclical attacks, tearing at reality with perpetual loops of destruction."
    looks = """
    Kboshi presents as a scholarly figure whose appearance belies the dangerous forces he commands. He carries himself with the bearing of an academic or researcher, someone more at home in a laboratory than on a battlefield—yet the dark energies that ripple at his fingertips make it clear he's no stranger to conflict. His build is lean rather than imposing, with the physique of someone who spends more time in study and experimentation than in physical training, though there's a wiry strength in his frame that shouldn't be underestimated.

    His most distinctive feature is his striking white hair, which stands in stark contrast to the shadows he manipulates. The hair is kept at a practical length, neither overly styled nor unkempt, often appearing slightly tousled as if he's been working late into the night on some arcane research. The pale color gives him an otherworldly quality, as though prolonged exposure to void energies has leached the natural pigment from his strands, leaving behind this ghostly shade. It frames a face marked by sharp, intelligent features—high cheekbones, a straight nose, and eyes that seem to pierce through surface details to examine the fundamental structures beneath. His gaze is analytical and probing, the look of someone constantly deconstructing and reconstructing reality in his mind.

    He wears a white lab coat that has become his signature garment—crisp, professional, and practical. The coat falls to mid-thigh, with long sleeves often rolled up to the forearms when he's working, revealing lean arms marked with faint scars or discolorations from experimental mishaps. The pristine white of the coat serves as a stark visual counterpoint to the dark, void-like energies he wields, creating an almost ironic juxtaposition between his appearance as a researcher and the destructive forces he commands. Beneath the coat, he typically wears simple, dark clothing—a fitted shirt and trousers in blacks or deep grays—utilitarian choices that don't distract from his work. The coat's pockets are often stuffed with small notebooks, writing implements, or curious artifacts gathered during his studies.

    Kboshi's movements are precise and deliberate, with the careful control of someone accustomed to handling volatile materials. He doesn't rush, doesn't waste energy on unnecessary gestures—every motion serves a purpose, whether it's adjusting his coat, gesturing while explaining a concept, or channeling dark energy into a devastating flux cycle. When he speaks, his voice is calm and measured, tinged with the detachment of a scientist discussing experimental results rather than the heat of battle. There's an air of cold curiosity about him, as if he views combat as another form of research, each engagement an opportunity to test his theories about entropy and void.

    Overall, Kboshi's appearance as a white-haired researcher in a lab coat creates a deceptive impression of harmlessness—an impression that shatters the moment dark vortexes begin to tear at reality around him. He is the embodiment of dangerous knowledge, a scholar who has peered into the void and emerged with the power to unravel existence itself, all while maintaining the composed demeanor of an academic at work.
    """
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type("Dark")
    )
    passives: list[str] = field(default_factory=lambda: ["kboshi_flux_cycle"])
