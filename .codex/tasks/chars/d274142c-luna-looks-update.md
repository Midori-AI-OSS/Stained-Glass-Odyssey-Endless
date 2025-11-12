# Task: Update Luna's Character Appearance Description

## Background
Luna Midori is a 6★ character with an existing detailed `looks` field in `backend/plugins/characters/luna.py` (lines 193-201). The current description covers her physical appearance, clothing, gear, and characteristic behaviors. This task updates that description with new visual direction provided by the project owner.

## Problem
The current `looks` description needs to be updated to reflect new character design direction or artistic refinement. The existing content is comprehensive but may need adjustment to align with updated visual references or narrative direction.

## Requested Changes
- Replace the existing `looks` field in `backend/plugins/characters/luna.py` (lines 193-201) with the new description provided below.
- Ensure the new description maintains proper Python string formatting (triple-quoted string).
- Preserve all other character attributes (name, full_about, summarized_about, etc.) unchanged.
- The description should focus on Luna's visual appearance, clothing, gear, and characteristic mannerisms.

## New Looks Description
**[PLACEHOLDER - Project owner will provide the updated appearance description here]**

Replace the current `looks` field starting at line 193 with the provided description.

## Acceptance Criteria
- The `looks` field in `backend/plugins/characters/luna.py` has been updated with the new description.
- The Python file syntax remains valid (no linting errors).
- All other character fields remain unchanged.
- The character still loads correctly in the game.
- Backend tests continue to pass without errors related to Luna's definition.

## Files to Modify
- `backend/plugins/characters/luna.py` - Update the `looks` field (line 193)

## Testing Notes
After updating:
```bash
cd backend
uv tool run ruff check backend/plugins/characters/luna.py
uv run pytest tests/ -k luna -v
```
