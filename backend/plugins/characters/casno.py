from dataclasses import dataclass, field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Casno(PlayerBase):
    """Fire-aligned gacha recruit who thrives on planned downtime."""

    id = "casno"
    name = "Casno"
    full_about: str = (
        "A stoic veteran pyrokinetic who has learned to weaponize recovery. "
        "Casno tallies Relaxed stacks with every five attacks; once the gauge "
        "overflows, he skips his next strike to breathe, cashing in five stacks "
        "for a self-heal and 15% base-stat boons per stack before erupting back into combat."
    )
    summarized_about: str = "A stoic veteran pyrokinetic who weaponizes recovery, taking tactical breaths to heal and strengthen before erupting back into combat."
    looks = """
    Casno is a human man in his mid-twenties who radiates controlled intensity and battle-hardened discipline. Standing with a powerful, athletic build, his physique speaks to years of training and combat—broad shoulders, defined musculature, and a solid stance that suggests both strength and unwavering stability. He moves with the economical precision of a veteran who has learned to conserve energy between engagements, never wasting motion, always ready to shift from rest to action in a heartbeat.

    His most striking feature is his vivid red hair, worn in a practical style that keeps it clear of his face during combat. The color is bold and unmistakable—a deep, flame-like crimson that seems almost symbolic of his pyrokinetic abilities. His face is angular and strong-jawed, with sharp features that rarely soften into expressions of levity. His eyes, often narrowed in concentration or assessment, carry the weight of someone who has seen conflict and survived it, maintaining a calm, analytical gaze even under pressure. There's a weathered quality to his features, subtle lines around his eyes and mouth that mark him as someone who has endured, adapted, and emerged stronger.

    Casno's attire is functional and unadorned, favoring practicality over aesthetics. He typically wears combat-ready gear suited for mobility and protection—fitted, durable fabrics in dark or neutral tones that won't hinder his movements or draw unnecessary attention. His clothing often shows the wear of field use: faint scorch marks near the sleeves or collar, minor repairs that speak to campaigns fought and endured. There's no decorative flair, no attempt to intimidate through appearance alone; his presence does that work for him. His hands, when visible, are calloused and scarred—evidence of a life spent wielding flame and steel in equal measure.

    His posture is steady and grounded, shoulders square, weight balanced as if perpetually ready to engage or retreat as tactics demand. He doesn't fidget or shift unnecessarily; when Casno is still, he is entirely still, embodying the discipline of controlled breathing and deliberate rest that defines his combat philosophy. When he moves, it's with purpose—measured steps, deliberate turns, every action calculated to preserve energy until the moment it's needed. In conversation, he speaks sparingly, his voice low and even, carrying the gravitas of someone who values action over words.

    Overall, Casno projects the image of a seasoned warrior who has learned to master not just his flames, but himself. His stoic demeanor, commanding build, and the telltale red hair mark him as a formidable presence on any battlefield—a man who understands that true power lies not in constant exertion, but in knowing when to push forward and when to breathe, heal, and prepare for the next engagement.
    """
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=lambda: load_damage_type("Fire"))
    passives: list[str] = field(default_factory=lambda: ["casno_phoenix_respite"])
    voice_gender = "male"


__all__ = ["Casno"]
