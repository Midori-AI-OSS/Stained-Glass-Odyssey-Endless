# Add Looks String to Persona Light and Dark Character

## Description
Add a `looks` field to the Persona Light and Dark character class (`backend/plugins/characters/persona_light_and_dark.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

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
- **Gender:** Male (referred to as "his")
- **Relationship:** Brother to Lady Light and Lady Darkness
- **Hair:** Black and white (salt and pepper) with black and white sparkles throughout
- **Apparent Age:** Appears ageless, but looks around the same age as Lady Light and Lady Darkness (approximately 23)
- **Special Feature:** Hair has the same salt-and-pepper sparkle effect as his sisters

## Acceptance Criteria
- [ ] `looks` field added to the Persona Light and Dark dataclass
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
