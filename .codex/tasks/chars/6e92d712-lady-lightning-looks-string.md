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
- [ ] `looks` field added to the Lady Lightning dataclass
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
