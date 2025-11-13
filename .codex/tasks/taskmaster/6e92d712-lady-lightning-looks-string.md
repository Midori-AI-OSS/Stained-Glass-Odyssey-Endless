# Add Looks String to Lady Lightning Character

## Description
Add a `looks` field to the Lady Lightning character class (`backend/plugins/characters/lady_lightning.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

## Background
The repository is standardizing character descriptions by adding a `looks` string that provides detailed visual descriptions for each character. This supports future AI-powered features and provides rich context for character appearance.

## Reference Examples
See these files for the expected format:
- `backend/plugins/characters/luna.py` (lines 193-201)
- `backend/plugins/characters/ryne.py` (lines 24-54)
- `backend/plugins/characters/lady_light.py` (lines 16-24)
- `backend/plugins/characters/lady_darkness.py` (lines 16-25)

## Appearance Description
**Character Details:**
- **Gender:** Woman
- **Hair:** Dark yellow-colored with bangs
- **Eyes:** Yellow
- **Outfit:** Yellow off-shoulder strapless dress
- **Expression:** Closed mouth, slightly crazed expression
- **Visual Effects:** Breathtaking with shimmering effect
- **Posture:** Walking
- **Lighting:** Dramatic lighting

**SDXL Prompt Reference:**
`(yellow off shoulder strapless+ dress), woman, (dark yellow- colored hair), bangs, closed mouth, (yellow- eyes)+, breathtaking--, shimmering-- effect, walking, dramatic lighting, slightly crazed expression`

## Acceptance Criteria
- [x] `looks` field added to the Lady Lightning dataclass
- [x] Content follows multi-paragraph format used in reference examples
- [x] Triple-quoted string format used for multiline text
- [x] Positioned after `summarized_about` and before `char_type`
- [x] No changes to existing functionality

## Task Type
Documentation / Character Enhancement

## Priority
Low - Quality of life improvement

## Notes
- This is part of a batch update to add looks strings to all characters
- User will provide the actual appearance description
- Task should only add the field, not modify any game mechanics

---

## Implementation Notes
**Completed:** 2025-11-13 (estimated based on code presence)
**Implemented by:** Coder Mode Agent (unmarked in task)

Added visual description covering:
- Woman in apparent thirties with crackling electrical presence
- Dark yellow hair (raw lightning color, wild, untamed, shimmering)
- Striking yellow eyes (electric, restless, constantly darting, manic intensity)
- Angular expressive face with closed mouth, weathered appearance
- Yellow off-shoulder strapless dress (vibrant, flowing, travel-worn, scorch marks)
- Breathtaking/shimmering effect per SDXL prompt
- Walking posture and dramatic lighting effects
- Slightly crazed expression integrated

Description successfully captures SDXL prompt details, manic energy, lab escape trauma, and lightning channeling abilities.

File location: `backend/plugins/characters/lady_lightning.py` (lines 28-35+)

---

## Audit Report
**Audited:** 2025-11-13  
**Auditor:** Auditor Mode Agent  
**Status:** ✅ **APPROVED** - Ready for taskmaster

### Verification Checklist
- ✅ `looks` field added to Lady Lightning dataclass (line 28)
- ✅ Content follows multi-paragraph narrative prose format (4,619 characters)
- ✅ Triple-quoted string format used correctly
- ✅ Positioned after `summarized_about` (line 27) and before `char_type`
- ✅ No changes to existing functionality (verified via character instantiation test)
- ✅ Linting passes with no errors (ruff check)
- ✅ Character loads successfully without errors
- ✅ Literary quality matches reference examples

### Code Quality Assessment
**Excellent implementation with psychological depth.** The description:
1. Uses narrative prose style consistent with reference examples
2. Captures all SDXL prompt details: dark yellow hair, yellow eyes, yellow off-shoulder dress, walking, dramatic lighting, slightly crazed expression, breathtaking/shimmering
3. Successfully integrates psychological trauma (lab escape, paranoia, manic energy)
4. Emphasizes restless, hypervigilant nature
5. Twin relationship to Lady Wind noted
6. Length (4,619 chars) appropriate for complexity

### Technical Validation
- Python syntax: Valid
- Field positioning: Correct
- SDXL prompt details accurately incorporated
- Character trauma and neurodivergence handled respectfully
- No regression in functionality

### Findings
**No issues found.** Implementation demonstrates strong character depth and accurate SDXL translation. Task was completed but never marked as such.

### Recommendation
**APPROVE** - Move to `.codex/tasks/taskmaster/` for completion tracking.
