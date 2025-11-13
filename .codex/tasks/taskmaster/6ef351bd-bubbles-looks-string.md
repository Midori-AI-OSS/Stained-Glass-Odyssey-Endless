# Add Looks String to Bubbles Character

## Description
Add a `looks` field to the Bubbles character class (`backend/plugins/characters/bubbles.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

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
- **Form:** A bubble
- **Note:** This is a literal bubble creature with no humanoid characteristics

## Acceptance Criteria
- [x] `looks` field added to the Bubbles dataclass
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

## Implementation Notes
**Completed:** 2025-11-13  
**Implemented by:** Coder Mode Agent

Added 6-paragraph visual description covering:
- Spherical bubble form (4' diameter) with opalescent translucent membrane
- Internal micro-bubbles as emotional/state indicators (drift patterns, formations)
- Fluid movement mechanics (floating, bouncing, spinning, pressure dynamics)
- Surface detail variations (swirling patterns, condensation, temporary dimple expressions)
- Bubble burst combat visuals (glowing micro-bubbles, satellite bubble ejection, chain reactions)
- Enthusiastic behavioral patterns (bouncing excitement, spinning joy, celebratory explosions)

Description creatively handles non-humanoid bubble creature while maintaining literary quality and capturing playful yet devastating combat nature.

File location: `backend/plugins/characters/bubbles.py` (lines 18-24)

---

## Audit Report
**Audited:** 2025-11-13  
**Auditor:** Auditor Mode Agent  
**Status:** ✅ **APPROVED** - Ready for taskmaster

### Verification Checklist
- ✅ `looks` field added to Bubbles dataclass (line 18)
- ✅ Content follows multi-paragraph narrative prose format (6 paragraphs, 5,540 characters)
- ✅ Triple-quoted string format used correctly
- ✅ Positioned after `summarized_about` (line 17) and before `char_type` (line 26)
- ✅ No changes to existing functionality (verified via character instantiation test)
- ✅ Linting passes with no errors (ruff check)
- ✅ Character loads successfully without errors
- ✅ Literary quality matches Luna/Lady Light reference examples

### Code Quality Assessment
**Outstanding creative implementation.** The description:
1. Successfully describes a non-humanoid character using narrative prose
2. Provides innovative solution for expressing emotions/personality without human features
3. Uses micro-bubble formations and membrane changes as visual communication
4. Covers physical form, movement, surface details, combat effects, and behavior
5. Maintains high literary quality with creative metaphors and vivid imagery
6. Character concept ("literally a bubble") handled with sophistication and depth
7. Total length (5,540 chars) appropriate and matches reference example standards

### Technical Validation
- Python syntax: Valid
- Import structure: Correct (dataclass pattern maintained)
- Field positioning: Correct (after `summarized_about`, before `char_type`)
- No regression in character loading or game functionality
- Documentation (player-foe-reference.md) already includes Bubbles
- Creative challenge (non-humanoid character) successfully resolved

### Findings
**No issues found.** Implementation demonstrates exceptional creativity and meets all acceptance criteria while pushing the boundaries of character description for non-humanoid entities.

### Recommendation
**APPROVE** - Move to `.codex/tasks/taskmaster/` for completion tracking.

