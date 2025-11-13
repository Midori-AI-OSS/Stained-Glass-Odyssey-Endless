# Add Looks String to Ally Character

## Description
Add a `looks` field to the Ally character class (`backend/plugins/characters/ally.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

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
- **Gender:** Female
- **Race:** Human
- **Apparent Age:** Mid-20s
- **Hair:** Blonde
- **Eyes:** Brown

## Acceptance Criteria
- [x] `looks` field added to the Ally dataclass
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

Added 7-paragraph visual description covering:
- Athletic build and tactical posture (5'7", mid-20s, efficient movement)
- Facial features with blonde hair and brown eyes
- Eye characteristics emphasizing analytical nature
- Tactical wardrobe (charcoal combat jacket, teal undershirt, cargo pants)
- Specialized gear (elemental focuses, interface bracer, datapad)
- Visual effects during ability activation (elemental circuitry, cascade overloads)
- Behavioral patterns (tactical callouts, micro-adjustments, combat analytics)

Description integrates character's tactical support role and overload abilities into visual presentation while maintaining literary quality matching Luna/Lady Light examples.

File location: `backend/plugins/characters/ally.py` (lines 18-26)

