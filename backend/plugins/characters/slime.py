from dataclasses import dataclass
from typing import ClassVar

from plugins.characters._base import PlayerBase


@dataclass
class Slime(PlayerBase):
    """Unobtainable training dummy that mirrors base player stats."""

    id = "slime"
    name = "Slime"
    full_about = "A basic training dummy that serves as a practice target, perfectly mirroring fundamental combat parameters without special abilities."
    summarized_about = "A basic training dummy for practice and testing."
    looks = """
    Slime is not so much a character as it is a living, amorphous entity—a blob of gelatinous matter that lacks any fixed form or defining features beyond its essential sliminess. Its appearance is fundamentally simple yet oddly mesmerizing, a creature reduced to pure elemental essence without the complications of limbs, face, or conventional anatomy.

    The most striking aspect of a slime is its color, which shifts and changes to reflect whatever damage type it has attuned to. When aligned with dark energies, it takes on a blackish-blue hue—deep and murky like the ocean at midnight, with subtle gradients that suggest depth within its translucent mass. Fire-aspected slimes glow with reds and oranges, their substance appearing to simmer and bubble with internal heat. Ice slimes shimmer in pale blues and whites, their surface frosty and crystalline. Lightning slimes crackle with yellows and electric blues, small sparks occasionally dancing across their surface. Each elemental affinity paints the slime in its signature palette, making it a living indicator of the forces it channels.

    On rare and special occasions, a slime manifests in a breathtaking rainbow coloration—a prismatic display where bands of color ripple and flow through its gelatinous form like oil on water. These rainbow slimes are particularly mesmerizing to watch, their colors shifting and blending as they move, creating hypnotic patterns that cycle through the entire visible spectrum. The rainbow variant seems to suggest a slime that has transcended single-element limitations or perhaps one that contains the potential for all elemental types at once.

    The slime's form is roughly ovoid or dome-shaped, sitting on the ground like a puddle that has decided to hold its shape through surface tension alone. It has no discernible front or back, no eyes or mouth, no appendages to speak of—just a continuous blob of semi-transparent goo. When it moves, it does so by extending pseudopods—temporary protrusions of its mass that reach forward, anchor, and then pull the rest of its body along in a slow, undulating crawl. The movement is almost hypnotic in its simplicity, like watching a very slow wave crash in extreme slow motion.

    The texture appears viscous and wet, with a glossy surface that catches and reflects light in unpredictable ways. Depending on its current state, it might appear more liquid and runny, spreading out into a wider puddle, or more gelatinous and firm, holding a taller, more compact shape. Small bubbles occasionally form within its translucent mass, rising slowly to the surface and popping with tiny, barely audible sounds. The slime leaves a faint trail of residue wherever it goes—not quite liquid, not quite solid, evaporating slowly after it passes.

    As a training dummy, the slime exists in a state of perfect passivity. It doesn't attack, doesn't defend itself with any particular vigor, and shows no signs of personality, emotion, or intent. It simply exists, providing a target for those who wish to practice their combat techniques against something that can absorb punishment without complaint or resistance. There's something oddly peaceful about its complete lack of ambition or awareness—it is content to be exactly what it is: a blob of elemental-colored goo, serving its purpose without question or complaint, a perfect canvas upon which warriors can paint their practice strikes.
    """
    gacha_rarity = 0
    ui_non_selectable: ClassVar[bool] = True
