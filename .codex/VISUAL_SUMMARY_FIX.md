# Visual Summary of the Fix

## Flow Diagram: Before vs After

### BEFORE (Buggy Behavior)
```
User clicks card/relic
    ↓
select_card/select_relic called
    ↓
Card/relic staged (staging["cards"] = [card])
awaiting_card = True
    ↓
User clicks "advance room" (or double-clicks)
    ↓
advance_room checks state
    ↓
awaiting_card = True? YES
    ↓
staged_cards empty? YES (race condition/timing)
    ↓
❌ ERROR: "Cannot advance room while rewards are pending"
    ↓
User stuck, cannot progress
```

### AFTER (Fixed Behavior)
```
User clicks card/relic
    ↓
select_card/select_relic called
    ↓
Card/relic staged (staging["cards"] = [card])
awaiting_card = True
    ↓
User clicks "advance room" (or double-clicks)
    ↓
advance_room checks state
    ↓
awaiting_card = True? YES
    ↓
staged_cards empty? YES (race condition/timing)
    ↓
card_choice_options exists? NO (reward already handled)
    ↓
✅ Clear awaiting_card flag
    ↓
✅ Save state
    ↓
✅ Continue to advance room
    ↓
User progresses successfully
```

## Decision Tree

```
                    advance_room called
                            ↓
                    Load current state
                            ↓
                ┌───────────┴───────────┐
                ↓                       ↓
        awaiting_card?              awaiting_relic?
                ↓                       ↓
            YES │ NO                YES │ NO
                ↓                       ↓
        staged_cards empty?     staged_relics empty?
                ↓                       ↓
            YES │ NO                YES │ NO
                ↓                       ↓
    card_choice_options?        relic_choices in snapshot?
                ↓                       ↓
        YES │ NO                    YES │ NO
            ↓   ↓                       ↓   ↓
          ERROR │                     ERROR │
                ↓                           ↓
        Clear flag                  Clear flag
        Save state                  Save state
                ↓                           ↓
                └───────────┬───────────────┘
                            ↓
                    All flags cleared?
                            ↓
                        YES │ NO
                            ↓   ↓
                            │ ERROR
                            ↓
                    Advance room
                    successfully
```

## Code Comparison

### Before
```python
# routes/ui.py (line 502-508)
if state.get("awaiting_card"):
    if not staged_cards:
        # Always error - no distinction between pending and handled
        return create_error_response("Cannot advance room while rewards are pending", 400)
```

### After
```python
# routes/ui.py (line 502-516)
if state.get("awaiting_card"):
    if not staged_cards:
        # Check if card selection is still pending (user hasn't chosen yet)
        # vs already handled (staged card was confirmed by another process)
        if state.get("card_choice_options"):
            return create_error_response("Cannot advance room while rewards are pending", 400)
        # No staged card and no choices means reward was already handled
        # Clear the flag and continue
        state["awaiting_card"] = False
        await asyncio.to_thread(save_map, run_id, state)
```

## Test Coverage Matrix

| Scenario | awaiting_card | staged_cards | card_choice_options | Expected Result |
|----------|--------------|--------------|---------------------|-----------------|
| User hasn't selected card | True | Empty | Exists | ❌ Error (correct) |
| User selected & confirmed | False | Empty | - | ✅ Advance (correct) |
| Race condition (stale flag) | True | Empty | None | ✅ Clear flag & advance (FIXED) |
| Card is staged | True | Has card | - | ✅ Auto-confirm & advance (existing) |

## Impact

### Before Fix
- Users blocked from advancing
- Error message confusing ("rewards pending" when already handled)
- Only workaround: restart game or reload page

### After Fix
- Graceful handling of edge cases
- Clear progression even with race conditions
- Maintains strict validation when choice is genuinely needed
- Better user experience overall
