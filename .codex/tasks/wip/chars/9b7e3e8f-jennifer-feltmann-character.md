# Task: Add Jennifer Feltmann Character to Roster

## Background
Jennifer Feltmann is a new playable character joining the AutoFighter roster. She is a high school teacher with Dark-type powers and educator-themed abilities. Her signature passive revolves around applying debilitating "bad student" effects that slow enemies down significantly.

## Character Overview

**Basic Information:**
- **ID:** `jennifer_feltmann` (or `feltmann` for brevity)
- **Display Name:** Jennifer Feltmann
- **Character Type:** B (Feminine frame)
- **Damage Type:** Dark
- **Gacha Rarity:** 5★ (standard gacha recruit)

**Character Details:**
- **Portrait/Visual Assets:** Reference photos provided below
  - **Classroom Photo:** https://github.com/user-attachments/assets/2e38dacd-269e-4dde-9972-c72da053eb20
  - **Outdoor Photo (with dog):** https://github.com/user-attachments/assets/9b0d1eb7-e529-4b4e-bd9f-2b0cb77dd6f0
- **Pronouns:** She/Her
- **Voice Gender:** Female mid-ranged
- **Profession:** High school programming/robotics teacher with 20+ years of teaching experience
- **Full About:** Jennifer Feltmann is a veteran high school programming and robotics teacher who has dedicated over twenty years to shaping young minds in technology. Her approach to teaching blends patient guidance with firm expectations—she believes every student can succeed with the right encouragement and structure. Beyond the classroom, she's the kind of mentor who remembers which student struggles with recursion and which one lights up at hardware projects. Her "bad student" abilities in combat are less about cruelty and more about the exhausting reality of managing a classroom full of teenagers who forgot their assignments again—manifesting as debilitating debuffs that grind enemies to a halt like a lecture on proper variable naming conventions.
- **Summarized About:** A veteran programming and robotics teacher who channels twenty years of classroom management into debilitating "bad student" debuffs that bring chaos to a grinding halt.
- **Looks Description:** [See detailed description below in "Looks" section]

## Looks (Character Appearance Description)

Jennifer Feltmann (High School Robotics Teacher)

SUBJECT — FACE & HEAD
- Age appearance: **mid-fifties**; soft, rounded features; warm, approachable face; natural freckles scattered across bridge of nose and upper cheeks.
- Eyes: **observant and kind**, often crinkled at corners in gentle smile; patient, knowing gaze; the kind of eyes that notice when someone needs help before they ask.
- Expression: warm, genuine smile showing teeth with lifted cheeks when happy; settles into thoughtful, kind baseline even when serious; never stern despite authority role.

HAIR
- Color: **long, thick silver-gray** (natural, fully owned with confidence).
- Length & shape: flows well past shoulders in soft, natural waves; clean and well-kept with healthy shine.
- Styling details: **two options** — loose and flowing over one shoulder (elegant, relaxed), OR woven into **two thick braids** tied with **colorful yarn strips** (yellows, purples) for practical/outdoor work; braided style adds playful, whimsical touch.

BODY & PROPORTION
- Build: **average height, soft and sturdy**; strong in the way of people on their feet all day; not athletic but capable; reliable presence.
- Posture: relaxed but attentive; shoulders back, unhurried but purposeful; comfortable being the steady adult in the room.
- Skin: fair with healthy glow; natural freckles add endearing, human quality.

COSTUME — ADAPTABLE BETWEEN PROFESSIONAL AND CASUAL
**Professional/Classroom Mode:**
- Primary garment: **solid-colored tops** (blues, muted tones); V-neck or structured collar; clean lines.
- Silhouette: semi-formal, practical; comfortable for six-hour workday of teaching and troubleshooting.
- Footwear: **sturdy boots or shoes** designed for standing and moving; function over fashion.
- Overall aesthetic: competent and approachable; professional enough for conferences, comfortable enough for hands-on work.

**Casual/Off-Duty Mode:**
- Soft sweaters, practical jackets, comfortable layers.
- Clothes that can handle dirt or weather without complaint.
- Same sturdy footwear approach.

TEXTURE & MATERIAL DIRECTIONS
- Clothing is clean and well-kept but never fussy; values function and authenticity over fashion trends.
- Fabric reads as practical and comfortable; appropriate for both teaching environments and outdoor activities.
- Hair has natural shine and movement; silver-gray color catches light beautifully.
- When braided, colorful yarn ties provide vibrant accent (suggest yarn texture visible in close-ups).

OVERALL IMPRESSION
Grounded warmth and quiet competence. The teacher students remember fondly years later—patient, caring, believes in your potential. Maternal, protective energy without being overbearing. Draws people in through genuine care and competence rather than theatrics. In battle, channels exhausting familiarity of managing classroom chaos into debilitating debuffs that grind enemies to a halt.

## Signature Passive: "Bad Student" Debuff

**Passive ID:** `feltmann_bad_student` (or similar thematic name like `jennifer_disciplinary_action`)

**Theme:** As a high school teacher, Jennifer can apply disciplinary effects that dramatically slow down troublesome opponents (represented as "bad students").

**Mechanic Overview:**
- Applies a debuff to enemy targets that significantly reduces their speed/action economy
- Tier scaling makes the effect increasingly punishing at higher difficulties
- **Trigger Mechanism:** Chance-based on Jennifer's Effect Hit stat
  - **Normal attacks:** 5% of Effect Hit rate (e.g., 400% Effect Hit = 20% chance to apply debuff)
  - **Ultimate ability:** 150% of Effect Hit rate (e.g., 400% Effect Hit = 600% = guaranteed application with overflow)
- Single target application per attack

**Tier Scaling:**
- **Normal:** 75% speed reduction
- **Prime:** 150% speed reduction (enemies may skip actions entirely)
- **Glitched:** 500% speed reduction (enemies are nearly immobilized)

**Implementation Notes:**
- Create passive in appropriate tier folders:
  - `backend/plugins/passives/normal/feltmann_bad_student.py`
  - `backend/plugins/passives/prime/feltmann_bad_student.py`
  - `backend/plugins/passives/glitched/feltmann_bad_student.py`
- Debuff should apply a negative speed/action modifier via `StatEffect`
- Consider visual feedback for affected enemies (UI flag or icon)
- **Trigger Logic:**
  - Hook into `on_attack` or `hit_landed` event
  - Calculate application chance: `target.effect_hit * 0.05` for normal attacks
  - For ultimate: `target.effect_hit * 1.50` for guaranteed application
  - Roll random chance and apply debuff if successful
  - Debuff affects target's speed/actions_per_turn stat

## Implementation Checklist

### 1. Character Plugin File
**File:** `backend/plugins/characters/jennifer_feltmann.py` (or `feltmann.py`)

```python
from dataclasses import dataclass, field
from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.dark import Dark

@dataclass
class JenniferFeltmann(PlayerBase):
    id = "jennifer_feltmann"
    name = "Jennifer Feltmann"
    full_about = "Jennifer Feltmann is a veteran high school programming and robotics teacher who has dedicated over twenty years to shaping young minds in technology. Her approach to teaching blends patient guidance with firm expectations—she believes every student can succeed with the right encouragement and structure. Beyond the classroom, she's the kind of mentor who remembers which student struggles with recursion and which one lights up at hardware projects. Her 'bad student' abilities in combat are less about cruelty and more about the exhausting reality of managing a classroom full of teenagers who forgot their assignments again—manifesting as debilitating debuffs that grind enemies to a halt like a lecture on proper variable naming conventions."
    summarized_about = "A veteran programming and robotics teacher who channels twenty years of classroom management into debilitating 'bad student' debuffs that bring chaos to a grinding halt."
    looks = """
    [See "Looks (Character Appearance Description)" section in task file for full prose description]
    """
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Dark)
    passives: list[str] = field(default_factory=lambda: ["feltmann_bad_student"])
    
    def __post_init__(self) -> None:
        super().__post_init__()
        # TODO: Customize base stats if needed (HP, attack, defense, etc.)
        # Default stats from PlayerBase: 1000 HP, 100 atk, 50 def
        self.hp = self.max_hp
```

**Key Decisions Made:**
- Character ID: `jennifer_feltmann` (full name for clarity)
- Pronouns: she/her
- Voice: Female mid-ranged
- Stats: Use defaults initially (can be customized later if needed)

### 2. Normal Tier Passive
**File:** `backend/plugins/passives/normal/feltmann_bad_student.py`

**Requirements:**
- Apply 75% speed reduction to enemies when debuff is successfully applied
- **Trigger:** On attack with 5% of Effect Hit rate chance
  - Example: 400% Effect Hit = 20% chance per normal attack
- **Trigger on Ultimate:** 150% of Effect Hit rate (near-guaranteed)
  - Example: 400% Effect Hit = 600% chance (100% guaranteed with overflow)
- Duration: [DECISION NEEDED - suggest 2-3 turns or until combat ends]
- Single target per attack
- Use `StatEffect` with negative speed/actions_per_turn modifier

**Implementation Pattern:**
```python
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats

@dataclass
class FeltmannBadStudent:
    plugin_type = "passive"
    id = "feltmann_bad_student"
    name = "Bad Student"
    trigger = "on_attack"  # or "hit_landed"
    
    async def on_attack(self, attacker: "Stats", target: "Stats", damage: int, **kwargs) -> None:
        """Apply bad student debuff based on effect hit chance."""
        # Check if this is an ultimate (could use kwargs or check attack type)
        is_ultimate = kwargs.get("is_ultimate", False)
        
        # Calculate application chance
        effect_hit = attacker.effect_hit
        if is_ultimate:
            chance = effect_hit * 1.50  # 150% for ultimate
        else:
            chance = effect_hit * 0.05  # 5% for normal attack
        
        # Roll for application
        if random.random() * 100 < chance:
            # Apply 75% speed reduction
            debuff = StatEffect(
                name=f"{self.id}_debuff",
                stat_modifiers={"actions_per_turn": -0.75},  # or speed stat
                duration=3,  # 3 turns
                source=self.id,
            )
            target.add_effect(debuff)
```

### 3. Prime Tier Passive
**File:** `backend/plugins/passives/prime/feltmann_bad_student.py`

**Requirements:**
- Extend normal tier with 150% speed reduction
- May need to skip enemy actions entirely at this level
- Consider if this should prevent enemy turns completely

### 4. Glitched Tier Passive
**File:** `backend/plugins/passives/glitched/feltmann_bad_student.py`

**Requirements:**
- Extreme 500% speed reduction
- Enemies should be nearly or completely immobilized
- May need special handling for this extreme value

### 5. Documentation Updates
**File:** `.codex/implementation/player-foe-reference.md`

Add Jennifer Feltmann to the character roster table with:
- Character name, rank (B), rarity (5★), element (Dark)
- Signature trait description (`feltmann_bad_student` with tier scaling)
- Availability (Standard gacha recruit)

**Example Entry:**
```markdown
| Jennifer Feltmann | B | 5★ | Dark | `feltmann_bad_student` applies disciplinary debuffs that slow enemies: 75% (normal), 150% (prime), 500% (glitched) speed reduction. | Standard gacha recruit. |
```

### 6. Visual Assets

**Reference Photos:**
- **Classroom Photo:** https://github.com/user-attachments/assets/2e38dacd-269e-4dde-9972-c72da053eb20
  - Shows Jennifer in her professional teaching environment
  - Blue V-neck top, long silver-gray hair loose over one shoulder
  - Indoor lighting, structured setting
  
- **Outdoor Photo (with dog):** https://github.com/user-attachments/assets/9b0d1eb7-e529-4b4e-bd9f-2b0cb77dd6f0
  - Shows Jennifer outdoors on a hiking trail with her dog
  - Hair in two braids with colorful yarn ties (yellow and purple)
  - Casual outdoor attire, bright smile
  - Natural lighting

**Assets to Create:**
- Character portrait/avatar for gacha and party selection (use reference photos as basis)
- Battle sprite or character model
- Any special effect visuals for "bad student" debuff (suggestion: chalk dust, ruler, or detention slip icon)
- UI icon for debuff status effect

### 7. Testing
**File:** `backend/tests/test_jennifer_feltmann.py` (or similar)

**Test Coverage:**
- Character instantiation and base stats
- Passive application and debuff effects
- Tier scaling verification (75% → 150% → 500%)
- Integration with battle system
- Gacha system inclusion (5★ rarity)

## Design Questions for Coder (Remaining Decisions)

The following details still need to be finalized during implementation:

1. **Debuff Duration:**
   - How long should the "bad student" debuff last?
   - Suggestion: 2-3 turns for normal attacks, longer for ultimate
   - Should it stack if applied multiple times, or refresh duration?

2. **Stat Customization:**
   - Should Jennifer have custom base stats, or use defaults (1000 HP, 100 atk, 50 def)?
   - Any special stat growth patterns? (e.g., high effect hit to synergize with her passive)
   - Preferred aggro value?

3. **Additional Abilities:**
   - Any other teacher-themed abilities beyond "bad student"?
   - Special ultimate ability concept (already triggers debuff at 150% rate)?
   - Synergies with other characters?

4. **Visual Effects:**
   - What icon/particle effect should represent the "bad student" debuff?
   - Suggestions: chalk dust cloud, ruler, detention slip, or red pen mark
   - Color scheme for effects (to match Dark element)?

## Dependencies / Order

- **Blocked by:** None - all required information has been provided
- **Blocks:** None (this is a new character addition)
- **Priority:** MEDIUM-HIGH - Ready for implementation by Coder

## Acceptance Criteria

- [ ] Character plugin file created in `backend/plugins/characters/jennifer_feltmann.py`
- [ ] All three tier passives implemented (normal, prime, glitched) with proper Effect Hit scaling
- [ ] Character added to gacha system with 5★ rarity
- [ ] Documentation updated in `.codex/implementation/player-foe-reference.md`
- [ ] Visual assets created based on reference photos
- [ ] Character instantiates correctly with Dark damage type and Type B
- [ ] "Bad student" passive applies appropriate speed reduction per tier (75%/150%/500%)
- [ ] Passive triggers correctly: 5% of Effect Hit for normal attacks, 150% for ultimate
- [ ] All tests pass including new character-specific tests
- [ ] Foe variant auto-generated via `CHARACTER_FOES` system
- [ ] Character appears in gacha pool and can be recruited
- [ ] Voice metadata set to female mid-ranged

## Implementation Notes

**Code Style:**
- Follow existing character plugin patterns (see `carly.py`, `ixia.py`, etc.)
- Use dataclass decorator and inherit from `PlayerBase`
- Import Dark damage type from `plugins.damage_types.dark`
- Keep placeholder strings clearly marked with `[PLACEHOLDER]` prefix

**Passive Implementation:**
- Reference existing tier passive examples (see Luna passives)
- Use `StatEffect` for applying debuffs
- Consider diminishing returns if speed reduction exceeds 100%
- May need special handling for immobilization at 500% reduction

**Testing Strategy:**
- Start with basic instantiation tests
- Add passive mechanic tests once trigger logic is defined
- Integration tests with battle system once mechanics are finalized

**Incremental Approach:**
This task is ready for implementation:
1. **Phase 1:** Character plugin file with all confirmed details ✅ READY
2. **Phase 2:** Passive implementation with Effect Hit scaling ✅ READY
3. **Phase 3:** Visual assets based on reference photos ✅ READY
4. **Phase 4:** Testing and balancing

## Related Documentation

- `.codex/implementation/player-foe-reference.md` - Character roster reference
- `.codex/implementation/character-types.md` - Character type system
- `backend/plugins/characters/_base.py` - PlayerBase reference
- `backend/plugins/passives/` - Passive plugin examples
- `.codex/implementation/tier-passive-system.md` - Tier passive mechanics

## Notes

- Reference photos provided for visual asset creation
- Dark type chosen for thematic fit with "disciplinary" teacher concept
- Effect Hit scaling makes her passive more effective as she levels up and gains gear
- Speed reduction percentages are extreme at higher tiers - may need balancing after testing
- Ultimate ability provides near-guaranteed debuff application (150% of Effect Hit)
- Character backstory emphasizes patient mentorship rather than harsh discipline
- Silver-gray hair is a key visual identifier, along with optional braided style
- Classroom management theme translates to crowd control via debuffs
