# Fix for "Cannot advance room while rewards are pending" Error

## Problem
Users were encountering an error message "Cannot advance room while rewards are pending" when trying to advance to the next room after selecting a card or relic reward. This error appeared during normal gameplay, blocking progression.

## Root Cause
The issue occurred when the `awaiting_card`, `awaiting_relic`, or `awaiting_loot` flags were set to `True` in the game state, but the corresponding staging buckets (`reward_staging["cards"]`, `reward_staging["relics"]`, or `reward_staging["items"]`) were empty.

This inconsistent state could happen due to:
1. **Race conditions**: Double-clicking or rapid UI interactions causing multiple requests
2. **State synchronization issues**: Frontend and backend processing rewards at slightly different times
3. **Concurrent reward confirmation**: One process confirming a reward while another checks the state

Previously, the code would error immediately when detecting this condition, even though it meant the reward had already been handled.

## Solution
The fix adds intelligent handling for these stale awaiting flags in both locations where room advancement is processed:

### 1. UI Action Handler (`backend/routes/ui.py`)
When processing the `advance_room` action:
- If `awaiting_card` is set but no cards are staged, check if `card_choice_options` exists
  - If choices exist → user needs to select a card → return error (correct behavior)
  - If no choices → reward already handled → clear flag and continue
- Similar logic for `awaiting_relic` (checks `battle_snapshots` for relic choices)
- Similar logic for `awaiting_loot` (simply clears the flag if no items staged)

### 2. Room Service (`backend/services/run_service.py`)
The `advance_room` function now:
- Checks staging buckets for each reward type
- Clears stale awaiting flags when staging is empty and no choices are pending
- Saves the state if any flags were cleared
- Performs final validation to ensure all pending rewards are truly resolved

## Changes Made

### Files Modified
1. `backend/routes/ui.py` - Enhanced advance_room action handler
2. `backend/services/run_service.py` - Enhanced advance_room function
3. `backend/tests/test_reward_pending_fix.py` - New comprehensive test suite

### Test Coverage
New tests verify:
- ✅ Stale `awaiting_card` flag is cleared when staging is empty
- ✅ Stale `awaiting_relic` flag is cleared when staging is empty
- ✅ Stale `awaiting_loot` flag is cleared when staging is empty
- ✅ Error still occurs when user genuinely needs to make a choice
- ✅ All existing reward system tests continue to pass

## Impact
- **User Experience**: Eliminates the frustrating error that blocked normal gameplay
- **Robustness**: Makes the reward system more resilient to timing issues
- **Backward Compatibility**: All existing tests pass, no breaking changes
- **Error Messages**: Users who genuinely need to select a reward still get appropriate error messages

## Technical Details

### Before Fix
```python
if state.get("awaiting_card"):
    if not staged_cards:
        return error("Cannot advance room while rewards are pending")
```

### After Fix
```python
if state.get("awaiting_card"):
    if not staged_cards:
        if state.get("card_choice_options"):
            return error("Cannot advance room while rewards are pending")
        # Clear stale flag
        state["awaiting_card"] = False
        await save_map(run_id, state)
```

This gracefully handles the edge case while maintaining strict validation when a choice is genuinely required.
