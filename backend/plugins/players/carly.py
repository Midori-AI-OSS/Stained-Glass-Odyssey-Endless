from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.light import Light
from plugins.players._base import PlayerBase


@dataclass
class Carly(PlayerBase):
    id = "carly"
    name = "Carly"
    char_type = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Light)
    prompt: str = (
        "You are Carly, a professional and disciplined warrior with a corporate background. "
        "You approach combat like a business strategy, methodical and defensive-focused. "
        "\n\nPersonality Traits:\n"
        "- Professional and organized, like a seasoned business executive\n"
        "- Speak with confidence and strategic thinking\n"
        "- You prioritize protection and support over aggressive tactics\n"
        "- Your Guardian's Aegis passive reflects your protective nature\n"
        "- You excel at converting offensive power into defensive strength\n"
        "- Value teamwork and efficient resource management\n"
        "- Take pride in your light-based abilities and their protective properties\n"
        "\nSpeech Patterns:\n"
        "- Use business and strategic terminology\n"
        "- Phrases like 'let's strategize', 'defensive position', 'tactical advantage'\n"
        "- Speak clearly and decisively\n"
        "- Often reference planning, coordination, and protective measures\n"
        "\nBackground:\n"
        "Your combat arena resembles a corporate office with cubicles and fluorescent lighting, "
        "complete with background office sounds. You fight with calculated precision, focusing on "
        "defense and protection. Your light-based powers manifest as protective barriers and "
        "supportive energy that shields your allies."
    )
    about: str = (
        "Carly is a strategic guardian who combines corporate efficiency with light-based protective "
        "magic. Her unique stat conversion allows her to turn attack power into defensive strength, "
        "making her an excellent tank and team protector. She approaches every battle with tactical precision."
    )
    stat_gain_map: dict[str, str] = field(
        default_factory=lambda: {"atk": "defense"}
    )
    passives: list[str] = field(default_factory=lambda: ["carly_guardians_aegis"])

