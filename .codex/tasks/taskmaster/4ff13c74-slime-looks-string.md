# Add Looks String to Slime Character

## Description
Add a `looks` field to the Slime character class (`backend/plugins/characters/slime.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

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
- **Form:** Slime creature
- **Coloring:** Matches damage type color (e.g., dark damage type appears blackish-blue)
- **Special Variant:** Can sometimes be rainbow-colored
- **Note:** Visual appearance is dynamic and changes based on the slime's damage type

## Acceptance Criteria
- [x] `looks` field added to the Slime dataclass
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

Added 6-paragraph visual description covering:
- Amorphous gelatinous entity without fixed form
- Dynamic color shifting based on damage type (blackish-blue for dark, red-orange for fire, etc.)
- Special rainbow variant with prismatic coloration
- Ovoid/dome-shaped form with pseudopod movement mechanics
- Viscous, glossy texture with internal bubbles
- Perfect passivity as training dummy (no personality, pure function)

Description creatively handles non-humanoid slime creature while capturing elemental color variations and training dummy role.

File location: `backend/plugins/characters/slime.py` (lines 15-27)

---

## Audit Report
**Audited:** 2025-11-13  
**Auditor:** Auditor Mode Agent  
**Status:** ✅ **APPROVED** - Ready for taskmaster

### Verification Checklist
- ✅ `looks` field added to Slime dataclass (line 15)
- ✅ Content follows multi-paragraph narrative prose format (6 paragraphs, 3,436 characters)
- ✅ Triple-quoted string format used correctly
- ✅ Positioned after `summarized_about` (line 14) and before `gacha_rarity` (line 28)
- ✅ No changes to existing functionality (verified via character instantiation test)
- ✅ Linting passes with no errors (ruff check)
- ✅ Character loads successfully without errors
- ✅ Literary quality matches reference examples

### Code Quality Assessment
**Outstanding creative implementation.** The description:
1. Successfully describes non-humanoid slime creature using narrative prose
2. Captures key details: color matches damage type (dark = blackish-blue), rainbow variant possible
3. Provides rich sensory details for amorphous entity
4. Covers form, movement, texture, elemental variations
5. Emphasizes training dummy role with passive, purposeful existence
6. Length (3,436 chars) appropriate for scope

### Technical Validation
- Python syntax: Valid
- Field positioning: Correct (note: before `gacha_rarity` due to different class structure)
- Character details accurately implemented per task specification
- Non-humanoid challenge successfully handled
- No regression in functionality

### Findings
**No issues found.** Implementation complete and demonstrates creative excellence for non-humanoid character. Task was completed but never marked as such.

### Recommendation
**APPROVE** - Move to `.codex/tasks/taskmaster/` for completion tracking.
