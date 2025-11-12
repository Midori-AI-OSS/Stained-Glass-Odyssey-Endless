# Add Looks String to Becca Character

## Description
Add a `looks` field to the Becca character class (`backend/plugins/characters/becca.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

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
- **Apparent Age:** Mid-20s
- **Hair:** Blonde with blue ombre ponytail
- **Eyes:** Purple
- **Build:** Slender
- **Skin:** Fair and smooth with freckles on nose and cheeks
- **Makeup:** Light
- **Outfit:** Space strapless loose sundress
- **Accessory:** Paintbrush

**SDXL Prompt Reference:**
`(blonde-- with blue--- ombre-- ponytail hair)++, (purple- eyes)++, (female), (mid 20s), (slender build), (fair and smooth skin), (freckles on nose and cheeks), (light makeup), (space+ strapless lose sundress)+++, (paint brush)++`

## Acceptance Criteria
- [ ] `looks` field added to the Becca dataclass
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
