# Task: Update Lady Light's Character Appearance Description

## Background
Lady Light is a 5★ Aasimar character with an existing detailed `looks` field in `backend/plugins/characters/lady_light.py` (lines 16-24). The current description covers her appearance as someone battling Cotard's Syndrome, with distinctive white hair containing black starlike flecks, asymmetrical features, and protective light barriers. This task updates that description with new visual direction provided by the project owner.

## Problem
The current `looks` description needs to be updated to reflect new character design direction or artistic refinement. The existing content provides extensive visual and thematic details but may need adjustment to align with updated visual references or narrative direction.

## Requested Changes
- Replace the existing `looks` field in `backend/plugins/characters/lady_light.py` (lines 16-24) with the new description provided below.
- Ensure the new description maintains proper Python string formatting (triple-quoted string).
- Preserve all other character attributes (id, name, full_about, summarized_about, char_type, gacha_rarity, etc.) unchanged.
- The description should focus on Lady Light's visual appearance, attire, and characteristic presence.

## New Looks Description
**[PLACEHOLDER - Project owner will provide the updated appearance description here]**

Replace the current `looks` field starting at line 16 with the provided description.

## Acceptance Criteria
- The `looks` field in `backend/plugins/characters/lady_light.py` has been updated with the new description.
- The Python file syntax remains valid (no linting errors).
- All other character fields remain unchanged.
- The character still loads correctly in the game.
- Backend tests continue to pass without errors related to Lady Light's definition.

## Files to Modify
- `backend/plugins/characters/lady_light.py` - Update the `looks` field (line 16)

## Testing Notes
After updating:
```bash
cd backend
uv tool run ruff check backend/plugins/characters/lady_light.py
uv run pytest tests/ -k lady_light -v
```
