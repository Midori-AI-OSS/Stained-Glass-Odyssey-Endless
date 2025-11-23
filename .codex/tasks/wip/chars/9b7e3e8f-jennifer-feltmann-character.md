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

**Placeholder Information (to be filled in by user):**
- **Portrait/Visual Assets:** User will provide photos after task creation
- **Full About:** [PLACEHOLDER - awaiting user input for detailed backstory]
- **Summarized About:** [PLACEHOLDER - awaiting user input for short description]
- **Looks Description:** [PLACEHOLDER - awaiting user input for detailed appearance description]
- **Voice Sample/Gender:** [PLACEHOLDER - awaiting user input if needed]

## Signature Passive: "Bad Student" Debuff

**Passive ID:** `feltmann_bad_student` (or similar thematic name like `jennifer_disciplinary_action`)

**Theme:** As a high school teacher, Jennifer can apply disciplinary effects that dramatically slow down troublesome opponents (represented as "bad students").

**Mechanic Overview:**
- Applies a debuff to enemy targets that significantly reduces their speed/action economy
- Tier scaling makes the effect increasingly punishing at higher difficulties
- Should trigger on Jennifer's attacks or at regular intervals (design decision needed)

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
- May need custom trigger logic (e.g., on_attack, turn_start, or chance-based)

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
    id = "jennifer_feltmann"  # or "feltmann"
    name = "Jennifer Feltmann"
    full_about = "[PLACEHOLDER - awaiting detailed backstory from user]"
    summarized_about = "[PLACEHOLDER - awaiting short description from user]"
    looks = "[PLACEHOLDER - awaiting detailed appearance description and photos from user]"
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

**Key Decisions Needed:**
- Should the character ID be `jennifer_feltmann` or shortened to `feltmann`?
- Custom base stats or use defaults?
- Any additional passives beyond the signature "bad student" effect?
- Stat gain/loss maps for character progression?

### 2. Normal Tier Passive
**File:** `backend/plugins/passives/normal/feltmann_bad_student.py`

**Requirements:**
- Apply 75% speed reduction to enemies
- Trigger mechanism (on attack? turn start? chance-based?)
- Duration of debuff
- Stack behavior (single target? AoE? stacking debuffs?)
- Use `StatEffect` with negative speed modifier

**Placeholder Structure:**
```python
@dataclass
class FeltmannBadStudent:
    plugin_type = "passive"
    id = "feltmann_bad_student"
    name = "Bad Student"
    trigger = "[DECISION NEEDED: turn_start, on_attack, etc.]"
    
    async def apply(self, target, **kwargs):
        # Apply 75% speed reduction to enemy
        # Implementation details TBD
        pass
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

### 6. Visual Assets (User-Provided)
**Location:** `frontend/static/assets/portraits/` or similar

**Pending:**
- Character portrait/avatar images
- Any special effect visuals for "bad student" debuff
- UI icons if needed

### 7. Testing
**File:** `backend/tests/test_jennifer_feltmann.py` (or similar)

**Test Coverage:**
- Character instantiation and base stats
- Passive application and debuff effects
- Tier scaling verification (75% → 150% → 500%)
- Integration with battle system
- Gacha system inclusion (5★ rarity)

## Design Questions for User

Before implementation can be completed, please provide:

1. **Visual Assets:**
   - Character portrait/avatar images
   - Preferred image dimensions and format
   - Any special visual effects for abilities

2. **Backstory & Description:**
   - Full character backstory (`full_about` field)
   - Short summary for UI (`summarized_about` field)
   - Detailed appearance description (`looks` field)

3. **Passive Mechanic Details:**
   - Should "bad student" debuff trigger on every attack, or chance-based?
   - Single target or can affect multiple enemies?
   - How long should the debuff last? (1 turn? permanent until battle ends?)
   - Should it stack if applied multiple times?
   - Visual indicator needed for affected enemies?

4. **Stat Customization:**
   - Should Jennifer have custom base stats, or use defaults?
   - Any special stat growth patterns? (e.g., high defense, low attack)
   - Preferred aggro value?

5. **Additional Abilities:**
   - Any other teacher-themed abilities beyond "bad student"?
   - Special ultimate ability concepts?
   - Synergies with other characters?

6. **Character ID:**
   - Prefer `jennifer_feltmann` or shortened to `feltmann`?

## Dependencies / Order

- **Blocked by:** User-provided visual assets and detailed character information
- **Blocks:** None (this is a new character addition)
- **Priority:** MEDIUM - Can be implemented incrementally as information becomes available

## Acceptance Criteria

- [ ] Character plugin file created in `backend/plugins/characters/`
- [ ] All three tier passives implemented (normal, prime, glitched)
- [ ] Character added to gacha system with 5★ rarity
- [ ] Documentation updated in `.codex/implementation/player-foe-reference.md`
- [ ] Visual assets integrated (pending user submission)
- [ ] Character instantiates correctly with Dark damage type and Type B
- [ ] "Bad student" passive applies appropriate speed reduction per tier
- [ ] All tests pass including new character-specific tests
- [ ] Foe variant auto-generated via `CHARACTER_FOES` system
- [ ] Character appears in gacha pool and can be recruited

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
This task can be implemented in phases:
1. **Phase 1:** Character plugin skeleton with placeholders (READY NOW)
2. **Phase 2:** Visual assets and descriptions (PENDING USER INPUT)
3. **Phase 3:** Passive implementation once mechanics are finalized
4. **Phase 4:** Testing and balancing

## Related Documentation

- `.codex/implementation/player-foe-reference.md` - Character roster reference
- `.codex/implementation/character-types.md` - Character type system
- `backend/plugins/characters/_base.py` - PlayerBase reference
- `backend/plugins/passives/` - Passive plugin examples
- `.codex/implementation/tier-passive-system.md` - Tier passive mechanics

## Notes

- User will provide photos and additional details after task is started
- Dark type chosen for thematic fit with "disciplinary" teacher concept
- Alternative: Ice type could work for "cold" teacher personality
- Speed reduction percentages are extreme at higher tiers - may need balancing after testing
- Consider whether "bad student" is the in-game display name or if a more formal name is preferred
- Possible alternative passive names: "Disciplinary Action", "Detention", "After-School Correction", etc.
