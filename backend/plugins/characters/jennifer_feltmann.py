from dataclasses import dataclass, field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.dark import Dark


@dataclass
class JenniferFeltmann(PlayerBase):
    # Pronouns: She/Her
    # Display Name: Jennifer Feltmann (same as name)
    # Voice: Female mid-ranged
    id = "jennifer_feltmann"
    name = "Jennifer Feltmann"
    full_about = (
        "Jennifer Feltmann is a veteran high school programming and robotics teacher who "
        "has dedicated over twenty years to shaping young minds in technology. Her "
        "approach to teaching blends patient guidance with firm expectations—she believes "
        "every student can succeed with the right encouragement and structure. Beyond the "
        "classroom, she's the kind of mentor who remembers which student struggles with "
        "recursion and which one lights up at hardware projects. Her 'bad student' "
        "abilities in combat are less about cruelty and more about the exhausting reality "
        "of managing a classroom full of teenagers who forgot their assignments again—"
        "manifesting as debilitating debuffs that grind enemies to a halt like a lecture "
        "on proper variable naming conventions."
    )
    summarized_about = (
        "A veteran programming and robotics teacher who channels twenty years of "
        "classroom management into debilitating 'bad student' debuffs that bring chaos to "
        "a grinding halt."
    )
    looks = """
    Jennifer Feltmann carries the kind of grounded warmth that instantly reads as "trusted adult"—the steady mentor who has shepherded twenty graduating classes through finals week. She appears in her mid-fifties with soft, rounded features and a genuine smile that reaches the corners of her kind, observant eyes. Natural freckles scatter across the bridge of her nose and upper cheeks, lending a lived-in familiarity to her face. She projects patience and approachability even when she’s all business; her baseline expression is thoughtful, never stern.

    Her iconic silver-gray hair is long, thick, and meticulously kept. On professional days she lets it fall in loose, gleaming waves over one shoulder, catching classroom light like polished steel. Outside the lab she braids it into two thick plaits wrapped with colorful yarn ties—yellows, purples, and playful accents that hint at the whimsical teacher who runs after-school robotics clubs. Both looks feel deliberate; both say “I’ve shown up prepared.”

    Jennifer’s build is average height and sturdily grounded—the strength of someone who spends eight hours on her feet shepherding teenagers through coding demos. She has a relaxed but purposeful posture, shoulders back, gaze attentive, and hands that move with deliberate precision whether she’s handing out soldering irons or writing on a holo-board. Her skin carries a healthy fairness with the faint glow of someone who prefers afternoon hikes with her massive Irish Wolfhound when classes end.

    In the classroom she favors practical, solid-color tops—most famously a deep blue V-neck paired with dark slacks—layered with practical accessories like badge lanyards, smartwatch bands, and smudges of chalk dust. Outside, she swaps in a casual hiking jacket, jeans, and well-loved trail boots, trading faculty ID cards for braided hair ties and dog treats. Regardless of outfit, she always looks ready to pivot from gentle encouragement to “sit down and focus” authority in a heartbeat.

    Jennifer’s aura in battle mirrors her classroom presence: calm, anchored, and quietly relentless. She moves like someone pacing in front of a whiteboard, marking infractions with a patient sigh before leveling a glare that freezes the entire row. When her Dark-aligned abilities unfold, chalk dust whirls into sigil-lined detention slips, rulers snap into spectral metronomes, and invisible seating charts lock foes in place. Nothing about her look is flashy; instead, it’s the aesthetic of a beloved teacher who has absolute control over the room—and the room is the battlefield.
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Dark)
    passives: list[str] = field(default_factory=lambda: ["bad_student"])
    voice_gender = "female_midrange"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.hp = self.max_hp


__all__ = ["JenniferFeltmann"]
