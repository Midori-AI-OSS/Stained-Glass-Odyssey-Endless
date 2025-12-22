from dataclasses import dataclass, field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class LadyFireAndIce(PlayerBase):
    id = "lady_fire_and_ice"
    name = "LadyFireAndIce"
    full_about = "A legendary 6★ elemental master appearing to be 18-20 years old, whose reddish-blue hair reflects her dual nature. Living with Dissociative Schizophrenia, she experiences herself as two distinct elemental personas that work in perfect, devastating harmony. Her fire alignment runs so hot that she sleeps unclothed to manage the constant heat radiating from her body. In combat, her duality engine allows her to wield both fire and ice through seamless persona switches—one moment erupting with volcanic fury, the next freezing enemies with arctic precision. The opposing forces create devastating thermal shocks that few opponents can withstand."
    summarized_about = "A dual-natured elemental master who switches between volcanic fury and arctic precision, creating devastating thermal shocks."
    looks = """
    Lady Fire and Ice, known in quiet moments as Hannah, stands 5′5″ with an athletic build that speaks to constant motion and elemental tension. Her frame is toned yet feminine, with the kind of contained energy that radiates heat even at rest. At eighteen to twenty years old, she carries herself with the duality of youth and ageless power—one moment moving with teenage spontaneity, the next pivoting with the measured precision of someone who has witnessed epochs of elemental conflict within her own mind. Her skin has a warm, sun-kissed undertone on one side, while the other carries a cooler, almost porcelain quality, as if her dual elemental nature manifests subtly even in her complexion.
    Her most striking feature is her hair: thick, flowing locks that cascade past her shoulders in a mesmerizing gradient of reddish-blue. The color shifts depending on which persona is ascendant—flickering with ember-orange highlights when the fire side surges forward, deepening to frost-touched cobalt when ice takes command. The strands seem to hold residual elemental energy, occasionally releasing wisps of steam or frost particles that dissipate before reaching the ground. She keeps it loose and untamed, reflecting the wild harmony of her dual nature, though it moves with an almost sentient quality, responding to her emotional and elemental state.
    Her eyes are heterochromatic windows into her divided soul: the left burns with volcanic amber that flickers like banked coals, while the right gleams with glacial blue that catches light like winter ice. When she switches between personas, the dominant eye brightens while the other dims slightly, creating a visual cue to which force is currently ascendant. The gaze itself is intense and knowing, carrying the weight of two complete personalities observing the world simultaneously. Her facial features are delicate but strong—high cheekbones, a straight nose, and full lips that curl into confident smiles or fierce determination with equal ease.
    Due to her fire alignment running exceptionally hot, she favors minimal, practical clothing that won't trap heat. Her typical combat attire consists of form-fitting athletic wraps and breathable fabrics in colors that mirror her elemental duality—crimson and azure arranged in asymmetric patterns. One arm might bear a sleeve of red fabric while the other remains bare and traced with frost patterns. She wears sturdy boots designed to handle both scorched earth and frozen tundra, and her hands are often bare to allow direct elemental channeling. When not in combat, she wraps herself in loose, flowing robes that billow with the thermal currents she generates, creating a constant, dramatic silhouette.
    Elemental manifestations are her constant companions. When the fire persona is dominant, her skin radiates palpable heat, steam rises from her shoulders, and small flame motes dance around her fingertips. The air shimmers around her like summer asphalt, and her movements become sharp and explosive. When ice takes over, frost crystals form on her hair and lashes, her breath mists in the air regardless of temperature, and the ground beneath her feet develops a thin glaze. The transitions between states create dramatic temperature gradients—crackling thermal shocks that manifest as visible distortions in the air, swirling vortices where heat meets cold.
    Her mannerisms reflect her divided consciousness. She speaks in a voice that occasionally shifts mid-sentence, one persona finishing the thought of another with seamless coherence that belies the profound divide within. Her gestures can be contradictory—one hand reaching out with welcoming warmth while the other instinctively maintains guarded distance. Yet there's no confusion in her movements; rather, there's a strange, perfect synchronization, as if two expert dancers have learned to share a single body. In combat, this manifests as devastating combo attacks where fire and ice flow through her in alternating waves, each persona trusting the other completely. At rest, she exudes both comfort and caution: a living paradox of opposing forces in devastating harmony.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(["Fire", "Ice"]))
    )
    passives: list[str] = field(default_factory=lambda: ["lady_fire_and_ice_duality_engine"])
