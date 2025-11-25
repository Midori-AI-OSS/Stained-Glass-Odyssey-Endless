# Add Looks String to GrayGray Character

## Description
Add a `looks` field to the GrayGray character class (`backend/plugins/characters/graygray.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

## Background
The repository is standardizing character descriptions by adding a `looks` string that provides detailed visual descriptions for each character. This supports future AI-powered features and provides rich context for character appearance.

## Reference Examples
See these files for the expected format:
- `backend/plugins/characters/luna.py` (lines 193-201)
- `backend/plugins/characters/ryne.py` (lines 24-54)
- `backend/plugins/characters/lady_light.py` (lines 16-24)
- `backend/plugins/characters/lady_darkness.py` (lines 16-25)

## Acceptance Criteria
- [ ] `looks` field added to the GrayGray dataclass
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

## Suggested `looks` string (ready to paste into `graygray.py`)

Below is a multi-paragraph triple-quoted Python string that follows the repository's format. Paste it into the `Graygray` dataclass after `summarized_about` and before `char_type`.

```python
"""
A compact, athletic build with an approachable, practical presence. Her face is open and expressive—warm eyes that watch for patterns and a ready, rueful smile that suggests quiet confidence more than bravado. Her complexion is natural and unadorned; she favors a utilitarian, lived-in look over anything ornate.

;Hair falls to short/medium length, often tousled and casually swept to one side; the color reads as a soft, ashy blonde with darker roots. Her everyday wardrobe skews comfortable and functional: worn hoodies, simple tees, and relaxed jeans in muted tones (grays, faded blues, soft creams). A well-loved sweatshirt or hoodie is a common layer, the kind that looks like it has been lived in.

Small, informal accessories complete her silhouette—over-ear headphones often hang around her neck, and she sometimes wears a practical band or bracelet. Her posture is relaxed and thoughtful; she often sits with arms or legs crossed when mulling over a tactic, and she leans in when engaged, curious and attentive rather than theatrical.

Subtle, thematic visual effects accompany her focus: when she syncs to an opponent's rhythm or prepares a counter, faint silver-gray motes or musical-note-like glyphs gather briefly around her hands and shoulders. These are understated—an echo of tempo and timing rather than full spectacle—and they fade as quickly as they appear.
"""
```
