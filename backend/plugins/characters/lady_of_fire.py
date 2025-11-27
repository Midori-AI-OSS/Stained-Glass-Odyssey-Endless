from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.fire import Fire


@dataclass
class LadyOfFire(PlayerBase):
    id = "lady_of_fire"
    name = "LadyOfFire"
    full_about = "A fierce pyromancer appearing to be 18-20 years old, whose dark red hair flows like liquid flame and whose very presence exudes overwhelming warmth. Living with Dissociative Schizophrenia, she channels her condition into her fire magic, allowing different aspects of her psyche to fuel increasingly intense infernal momentum. Each enemy defeated feeds her inner flame, building heat waves that grow stronger with every victory. Her red eyes burn with hot intensity, and her fire magic seems to pulse with the rhythm of her fractured consciousness, creating unpredictable but devastatingly effective pyroclastic attacks."
    summarized_about = "A fierce pyromancer who channels her fractured consciousness into devastating fire magic, building infernal momentum with each victory."
    looks = """
    Lady of Fire—known variously as Persona Fire, Fire, or Lady Fire—is a young woman who appears to be around eighteen to twenty years old, radiating an intensity that seems to set the very air around her ablaze. Her most captivating feature is her long, flowing dark red hair, which cascades down her back and shoulders like molten lava frozen mid-pour. The color is deep and rich—not the bright crimson of fresh blood, but the darker, smoldering red of coals that have burned long into the night. The hair moves with a life of its own, flowing and rippling as if caught in invisible thermals rising from her body, creating the illusion that it's made of liquid flame rather than ordinary strands. Neat bangs frame her face, falling just above her eyebrows, providing a structured contrast to the wild flow behind.

    Her eyes are perhaps her most arresting feature—hot red irises that seem to burn with an inner fire. They're large and expressive, capable of shifting from fierce determination to distant contemplation in a heartbeat, reflecting the complex interplay of her consciousness. The intensity in those eyes is palpable; when she focuses on something, it's as if she's attempting to will it into combustion through sheer force of gaze. There's an unsettling quality to her stare at times, a flickering emptiness that suggests she's looking at something—or someone—that others cannot see, a visual manifestation of her condition. Yet despite this, there's also vulnerability there, a young woman navigating a world through fractured perceptions, using the only tools she has to make sense of it all.

    Her face is youthful and striking, with high cheekbones, a small straight nose, and soft features that retain the last traces of adolescence. She keeps her mouth closed most of the time, lips pressed together in a neutral expression that can shift rapidly to determination, confusion, or fierce concentration. Her complexion is fair but carries a perpetual warmth, as if heated from within, with a subtle flush to her cheeks that speaks of the fire constantly burning in her core. There's an ethereal, almost haunting quality to her beauty—the kind of face that would be serene if not for the storm of thoughts and identities swirling behind it.

    Lady of Fire wears a striking red strapless dress that hugs her form before flowing out in elegant folds, the fabric appearing as if it could be woven from solidified flame. The dress is simple in cut but dramatic in presence, the deep red color matching her hair and eyes, creating a cohesive visual theme of fire incarnate. Over this, she drapes a white cloak that provides stark contrast—pristine, flowing fabric that billows behind her when she moves, the edges occasionally catching hints of heat shimmer. The white cloak serves almost as a grounding element, a visual reminder of her humanity amidst all the flame and fury. The combination of red dress and white cloak creates an image of controlled chaos, passion restrained by will, fire contained but never truly tamed.

    Her presence is breathtaking in the most literal sense—there's a shimmering effect that surrounds her, the air itself seeming to waver and ripple with heat distortion. This effect intensifies during combat or when her emotions run high, creating an aura that makes her appear almost mirage-like at the edges. The warmth she exudes is not metaphorical; standing near her is like standing close to a bonfire, feeling the waves of heat radiating outward. This constant emission of warmth and the visual shimmer it creates give her an otherworldly quality, as if she's not entirely anchored to the physical plane.

    Her movements carry a fluid, almost hypnotic quality—graceful and deliberate when one aspect of her consciousness is in control, more erratic and unpredictable when different voices compete for dominance. She shifts between poised confidence and sudden hesitation, between serene focus and flickering uncertainty, her body language reflecting the internal dialogue constantly occurring within her fractured psyche. When she walks, the white cloak trails behind her dramatically, and her long hair flows in sympathy, creating a wake of movement that draws the eye.

    In combat, Lady of Fire transforms into something both terrifying and magnificent. The fire magic she channels pulses with irregular but powerful rhythms, flames erupting in patterns that seem chaotic yet somehow effective, as if different strategic minds are contributing to a single devastating whole. Her hot red eyes take on an even more intense glow, and the shimmering effect around her body intensifies to the point where she seems to flicker and dance like flame itself. Each defeated enemy feeds her internal fire, and you can see it in her bearing—she stands taller, burns brighter, the heat waves around her growing more pronounced with each victory.

    Overall, Lady of Fire presents as a breathtaking figure of elemental power filtered through the lens of a complex, fractured consciousness. She is young but ancient in the scope of her inner experience, beautiful but unsettling, powerful but unpredictable. The visual contrast of dark red hair and white cloak, of youthful features and burning eyes, of grace and chaos, creates an image that is impossible to forget—a pyromancer who doesn't just command fire, but embodies it in all its contradictory nature: destructive and purifying, chaotic and strangely focused, terrifying and utterly captivating.
    """
    gacha_rarity = 5
    char_type: CharacterType = CharacterType.B
    damage_type: DamageTypeBase = field(default_factory=Fire)
    passives: list[str] = field(default_factory=lambda: ["lady_of_fire_infernal_momentum"])
