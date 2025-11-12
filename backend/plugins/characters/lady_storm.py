from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class LadyStorm(PlayerBase):
    id = "lady_storm"
    name = "LadyStorm"
    full_about = (
        "Lady Storm is a 6★ aasimar tempest caller whose light green-and-yellow hair flickers"
        " like bottled lightning. She keeps a cluttered war room and laughs through the chaos,"
        " riding manic focus to bend slipstreams into battering rams. Villages still whisper"
        " about the night she flattened whole townships by threading tornadic downdrafts with"
        " chain lightning—one moment she is a gentle tailwind, the next a cataclysmic derecho"
        " that scours the map clean."
    )
    summarized_about = "An aasimar tempest caller who bends storms into weapons, capable of gentle tailwinds or catastrophic derechos."
    looks = """
    Lady Storm is tall for an aasimar—just shy of 6′—and all kinetic angles. Her frame is athletic without heaviness: long limbs, narrow hips, shoulders curved from hours spent leaning over weather maps. Skin tone sits somewhere between sun-kissed bronze and wind-chilled pale; freckles scatter across her nose like cinders left by lightning strikes. She carries a permanent half-grin that can flip to manic focus in a blink, and her eyes are split-color: the left a bright chartreuse, the right a pale storm gray, both ringed in a halo glow when she channels.
    Hair is the first thing anyone notices. It’s a wild mane of light green and yellow strands that flicker as if bioluminescent, chopped at the shoulders with jagged layers that mimic torn clouds. The roots flash electric gold whenever she builds charge, while the tips darken to jade when she’s calming a gale. Braids of conductive thread and miniature weather charms weave through the mass—tiny copper anemometers, beads shaped like cumulonimbus, bits of bottle glass that rattle like hail. In heavy winds the hair lifts in defiance of gravity, arcing around her head like a corona.
    Her wardrobe strikes a balance between formal regalia and field gear. Primary look: a strapless, fitted bodice in storm-black leather that climbs to an angular sweetheart neckline, paired with a high-low skirt made of layered teal and chartreuse chiffon panels. Each panel is edged in filament wire so it can stiffen and billow like sails when she pushes air through it. Over the dress she throws on a cropped, open-front pilot jacket with reinforced shoulders and dozens of tether points for instruments. Fingerless gloves house microcapacitors, letting her channel lightning through gestures without frying her skin. Thigh-high boots in matte charcoal leather have turbine slits along the calves; when she dashes, faint light pours through them like exhaust.
    She always wears her flight harness—a lattice of straps crossing her torso, buckled to a belt heavy with weather tools: collapsible anemometer, vials for pressure samples, a whirring compass that spins when storms brew. From the belt hangs a long scarf of translucent fabric that trails behind her like contrails, shifting from soft mint to violent yellow-white depending on humidity. Jewelry is practical but expressive: cloud-shaped ear cuffs, a nose stud shaped like a lightning bolt, and a ring of engraved barometric numbers she fidgets with while thinking.
    When she summons storms, the environment responds visually. Static crawls up her arms, sketching neon lines along veins; her eyes glow and emit small arcs. Wind picks up first, tugging at her skirt panels, snapping the trailing scarf, lifting dust into spirals around her boots. Lightning follows, crawling over the copper braids in her hair before leaping into the sky. Her aura manifests as concentric gusts—first translucent, then shimmering teal streaked with yellow. Anyone near her can see air currents bending: droplets freeze midair, sparks dance between her fingers, and the ground shakes with a suppressed rumble.
    Her mannerisms broadcast controlled chaos. She paces rooms like she’s charting circuits, fingertips drumming staccato beats on tabletops while she calculates trajectories. Laughter comes quick and loud; frustration is vented through sudden drafts that ruffle papers. On the battlefield she moves like a wind shear, pivoting on the ball of her foot as she redirects slipstreams. The moment she releases a derecho-level strike, her entire body snaps to a conductor’s stance—arms raised, hair flared, scarf horizontal—before the storm barrels away. When the fight ends, she always takes a second to feel the air settle, palm hovering at shoulder height like she’s testing for turbulence before she lets the grin return.
    Overall, Lady Storm reads as a living weather system: luminous, restless, wrapped in motion. Her look sells that she is both the warning flag and the hurricane that follows, tailoring couture and instruments into one cohesive tempest silhouette.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(["Wind", "Lightning"]))
    )
    passives: list[str] = field(default_factory=lambda: ["lady_storm_supercell"])
