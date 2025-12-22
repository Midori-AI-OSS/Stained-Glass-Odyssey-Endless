from dataclasses import dataclass, field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.wind import Wind


@dataclass
class LadyWind(PlayerBase):
    id = "lady_wind"
    name = "LadyWind"
    full_about = (
        "Persona Wind - Lady Wind is the twin sister of Lady Lightning, a"
        " female Aasimar whose ageless features hover somewhere between twenty"
        " and thirty-two. She lives in a perpetually messy aeromancy studio"
        " where scattered schematics and wind-torn journals reveal the manic"
        " focus that keeps her experiments spinning."
        " She stalks the halls in a green, off-shoulder strapless dress, her"
        " dark green crystal hair cropped with restless bangs above luminous"
        " green eyes. When she walks, a shimmering gale wraps around her,"
        " flecked with upset motes of blood that start red then slowly"
        " crystallize to green in midair, never touching the floor, and every"
        " step rings with the hum of the storm she keeps caged inside her ribs."
        " The lash of that captive wind leaves hairline cuts across her arms"
        " and shoulders—she is always bleeding as the wind around her cuts her,"
        " though the droplets spiral in place instead of falling, transforming"
        " from red to green crystals as they hang suspended."
        " Despite the chaos, she guards her allies with razor focus—layering"
        " wind wards, calming Lady Lightning's tempests, and whispering flight"
        " equations to anyone brave enough to listen."
    )
    summarized_about = "Lady Lightning's twin sister, an Aasimar aeromancer cloaked in bleeding winds who guards allies with precision despite her chaotic experiments."
    looks = """
    Lady Wind hovers in that ageless window between twenty and thirty-two, with the wiry, perpetual-motion build of someone who forgets to eat but never forgets to prototype. She stands about 5′7″, posture pitched slightly forward as if she’s forever leaning into headwinds. Skin tone is porcelain with a faint green luminescence along the veins, like light refracting through glass. Hairline cuts trace her arms, shoulders, and collarbone; each wound seeps blood that starts red but slowly crystallizes to green as it hangs suspended in the air, tethered by miniature whirlwinds rather than falling. The crystallizing droplets glow faintly, orbiting her like shards of stained glass in various stages of transformation from crimson to emerald.
    Her face is triangular with sharp cheekbones, a narrow nose, and restless lips that murmur flight equations under her breath. Eyes are a luminous emerald ringed in lighter jade, irises swirling when she’s plotting. Her pupils narrow vertically when she rides intense currents, giving her an almost draconic intensity. Dark green crystal hair is cut into an asymmetric bob: jagged bangs scraping across her brow, longer shards at the sides tapering to translucent tips that chime softly when the wind shifts. Each strand refracts light like faceted quartz, flashing bright whenever she pivots.
    Wardrobe is a precise mix of elegance and utility. She favors a strapless, off-shoulder dress in layered emerald silk, the bodice fitted to her ribs while the skirt splits at both thighs to allow maximum movement. Panels of translucent organza overlay the skirt, etched with faint aerodynamic equations that glow turquoise when she channels mana. A corseted waist belt in dark leather anchors instrument loops, while a bolero-length harness of metal filigree keeps focus stones hovering over her shoulder blades. Because the wind incessantly nicks her skin, the interior of the dress is lined with self-sealing mesh that shimmers like monofilament.
    Accessories double as lab equipment. She wears fingerless gloves threaded with silver contact points so she can sign commands directly into slipstreams. Anklets hide micro-gyros that keep her balanced during inverted maneuvers. Around her neck hangs a braided cord strung with miniature feathers of various flying creatures—each feather a promise of successful field tests. Ear cuffs shaped like weather vanes turn autonomously, giving an immediate read on air pressure changes. Footwear alternates between calf-strapped sandals for lab work and knee-high windrider boots with retractable winglets for combat.
    Her wind aura is tangible. A permanent gale coils around her, visible as a shimmering distortion seeded with the suspended blood droplets in various stages of crystallization—some still red, others transitioning through amber and jade tones, the oldest fully crystallized into glowing green shards. Every movement leaves contrails of sparkling particles; when she stands still (rare), the droplets align into helixes across her limbs, showcasing the full gradient from fresh red blood to finished green crystals. During combat the aura condenses into razor-thin sheets, slicing the air with audible chirps. When she overcharges, her crystal hair fractures light into a full halo and the cuts along her skin glow white-green, as if the wind is trying to carve new runes into her.
    Behavior betrays her manic brilliance. She wades through rooms strewn with schematics, trailing wind that flips pages and scatters loose quills. Fingers constantly trace sigils midair, leaving momentary glyphs that dissipate like smoke. She laughs abruptly when equations click, then clamps down into a razor-focused hush while she calibrates an ally’s wind ward. On the battlefield she circles allies in tight ellipses, layering invisible shields while muttering lift coefficients. When she has to bleed off excess gusts, she flares the skirt panels and lets the fabric snap like sails, all while the suspended blood glitters around her in its transformation from red to green like a warning halo.
    Altogether, Lady Wind looks like a living experiment: elegant chaos, crystalline hair, bleeding winds that crystallize in flight, and a mind that keeps the entire sky’s math spinning just behind her eyes.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Wind)
    passives: list[str] = field(default_factory=lambda: ["lady_wind_tempest_guard"])
