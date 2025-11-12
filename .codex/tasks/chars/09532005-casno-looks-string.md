# Add Looks String to Casno Character

## Description
Add a `looks` field to the Casno character class (`backend/plugins/characters/casno.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

## Background
The repository is standardizing character descriptions by adding a `looks` string that provides detailed visual descriptions for each character. This supports future AI-powered features and provides rich context for character appearance.

## Reference Examples
See these files for the expected format:
- `backend/plugins/characters/luna.py` (lines 193-201)
- `backend/plugins/characters/ryne.py` (lines 24-54)
- `backend/plugins/characters/lady_light.py` (lines 16-24)
- `backend/plugins/characters/lady_darkness.py` (lines 16-25)

## Placeholder - Appearance Description Needed
**User must provide:** Detailed visual description of Casno's appearance, including:
- Physical build and proportions
- Facial features and coloring
- Hair style, color, and length
- Clothing and outfit details
- Signature gear or accessories
- Posture and mannerisms
- Visual effects or magical elements

## Acceptance Criteria
- [ ] `looks` field added to the Casno dataclass
- [ ] Content follows multi-paragraph format used in reference examples
- [ ] Triple-quoted string format used for multiline text
- [ ] Positioned after `summarized_about` and before `char_type`
- [ ] No changes to existing functionality

## Task Type
Documentation / Character Enhancement

## Priority
Low - Quality of life improvement

## Notes
- This is part of a batch update to add looks strings to all characters
- User will provide the actual appearance description
- Task should only add the field, not modify any game mechanics
