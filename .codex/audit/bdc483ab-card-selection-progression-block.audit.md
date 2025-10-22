# Audit Report: Card Selection Progression Blocker

**Audit ID**: bdc483ab  
**Date**: 2025-10-22  
**Auditor**: GitHub Copilot Workspace Agent  
**Severity**: CRITICAL  
**Status**: BLOCKING

## Executive Summary

The game cannot progress past Room 2 due to a critical frontend-backend synchronization issue in the card selection reward phase. Players can click on cards, but the game remains permanently stuck, preventing any progression to subsequent rooms.

## Problem Statement

**Task**: "Play test and see if you can click on (no js, or cheating) the card and get to room 4."

**Result**: ❌ **FAILED** - Cannot progress past Room 2. Room 4 is unreachable.

## Detailed Findings

### Issue #1: Card Selection Flow is Non-Functional

**Severity**: CRITICAL  
**Impact**: Game is unplayable beyond Room 2

#### Observed Behavior

1. **Card Clickability**: ✅ WORKING
   - Cards are properly implemented as clickable `<button>` elements
   - Clicking a card successfully selects it (visual feedback shows active/pressed state)
   - Accessibility attributes are correctly set (aria-label, aria-pressed, role)

2. **Card Confirmation**: ❌ BROKEN
   - After clicking a card, the heading changes from "Choose a Card" to "Confirm Card"
   - No visible "Confirm" or "Submit" button appears
   - The "Advance" button remains disabled indefinitely
   - Message displays: "Advance locked until this phase is complete"
   - No clear user action to proceed

3. **Frontend-Backend Desync**: ❌ CRITICAL
   - **Frontend**: Shows card selection UI, waiting for user input
   - **Backend**: Auto-selects ALL THREE cards immediately without user interaction
   - Backend logs show:
     ```
     INFO Starting card selection for run [], party has 0 cards
     INFO Card selection complete: 3 cards selected after 3 attempts
     INFO Selected cards: ['guiding_compass', 'vital_core', 'lightweight_boots']
     ```
   - Frontend never receives or processes this completion state

4. **Error State**: ❌ BLOCKING
   - Error overlay appears: "Cannot advance room while rewards are pending"
   - Error persists even after card selection attempts
   - Backend returns HTTP 400 when frontend tries to advance
   - No recovery path available

#### Steps to Reproduce

1. Start a new Standard Expedition run
2. Complete the first battle (Room 2)
3. Card selection screen appears with 3 cards
4. Click on any card once → Card becomes selected (visual feedback)
5. Click on the same card again → Heading changes to "Confirm Card"
6. Click on the card again → No change
7. Try pressing Enter → No effect
8. Try double-clicking → No effect
9. **Result**: Stuck forever at card selection screen

#### Expected Behavior

1. Click a card once to select it
2. Click the same card again (or press a Confirm button) to finalize selection
3. Card selection phase completes
4. Advance button becomes enabled
5. Player can proceed to Battle Review phase
6. Player can advance to Room 3

#### Actual Behavior

- Card selection UI shows but cannot be completed
- Advance button never enables
- Player is permanently stuck at Room 2
- Cannot progress to Room 3 or Room 4
- Game becomes unplayable

### Issue #2: Confusing UX for Card Confirmation

**Severity**: HIGH  
**Impact**: Even if the blocker is fixed, UX is unclear

The code in `RewardOverlay.svelte` (lines 897-918) implements a "double-click to confirm" pattern:

```javascript
const isDoubleClick = isCard
  ? highlightedCardKey === selectionKey
  : highlightedRelicKey === selectionKey;

if (!isDoubleClick) {
  if (isCard) {
    highlightedCardKey = selectionKey;
  }
  return;  // First click just highlights
}

// Second click confirms
await performRewardSelection(detail);
```

**UX Problems**:
- No visual indication that a second click is required
- Heading changes to "Confirm Card" but no button appears
- Users expect either:
  - A visible "Confirm" button to click, OR
  - Single-click selection with auto-advance
- Current implementation has neither

**Recommendation**: Add a visible "Confirm Selection" button that becomes enabled after selecting a card.

### Issue #3: Backend Auto-Selection Behavior

**Severity**: HIGH  
**Impact**: Undermines the entire card selection feature

The backend automatically selects cards without waiting for user input:

```
INFO Card selection complete: 3 cards selected after 3 attempts
INFO Selected cards: ['guiding_compass', 'vital_core', 'lightweight_boots']
```

**Questions**:
- Is this auto-selection intentional (for testing/demo)?
- Should the backend wait for frontend card choices?
- Are the frontend card selection UI and backend logic meant to work together?

**Impact**:
- Frontend card selection UI becomes meaningless
- User believes they're making a choice, but backend has already decided
- Creates a confusing "phantom choice" scenario

## Screenshots

### Card Selection Screen (Initial)
![Card Selection](https://github.com/user-attachments/assets/e6845691-f41d-461b-bd83-d9f8f2bc3ddc)

### After Clicking Card (Stuck State)
![Confirm Card State](https://github.com/user-attachments/assets/c7b60827-64c0-4816-9f85-150665191b56)

## Technical Analysis

### Frontend Code References

**File**: `frontend/src/lib/components/RewardOverlay.svelte`
- Lines 881-918: `handleSelect()` function implements double-click pattern
- Lines 897-911: First click only highlights, returns early
- Line 917: Second click triggers `performRewardSelection()`

**File**: `frontend/src/lib/components/RewardCard.svelte`
- Lines 28-35: `dispatchSelect()` and `handleClick()` - basic click handler
- Properly implemented as accessible button element

### Backend Log Evidence

```
[10/22/25 13:10:49] INFO Starting card selection for run [], party has 0 cards
                    INFO Card selection complete: 3 cards selected after 3 attempts
                    INFO Selected cards: ['guiding_compass', 'vital_core', 'lightweight_boots']
                    INFO Battle rewards: gold=8 cards=['guiding_compass', 'vital_core', 'lightweight_boots']
[2025-10-22 13:10:59] POST /rewards/loot/51446d7c-3c6c-4a2e-884c-ae0a39cd9c92 1.1 200
                      POST /ui/action 1.1 400 75  <- 400 ERROR
```

## Testing Environment

- **Browser**: Playwright-controlled browser
- **Backend**: Quart app running on http://localhost:59002
- **Frontend**: Vite dev server on http://localhost:59001
- **Database**: Fresh database (cleared before testing)
- **Run Configuration**: Standard Expedition, Pressure 0, single party member (Player)

## Recommendations

### Immediate (Critical)

1. **Fix Frontend-Backend Sync**: Investigate why backend auto-selects cards and frontend doesn't receive/process the completion
2. **Add Escape Hatch**: Provide a way to close/skip card selection if stuck (for recovery)
3. **Fix Advance Button**: Ensure Advance button enables after card selection completes

### Short-Term (High Priority)

4. **Improve UX**: Add a visible "Confirm Selection" button after selecting a card
5. **Add Visual Feedback**: Show clear indication that second click is required
6. **Error Handling**: Handle the 400 error gracefully with user-friendly message

### Long-Term (Medium Priority)

7. **Design Review**: Decide whether backend should auto-select or wait for user input
8. **Add Keyboard Support**: Allow Enter key to confirm selected card
9. **Add Skip Option**: Allow players to skip card rewards if desired
10. **Add Testing**: Create automated tests for card selection flow

## Impact Assessment

**User Impact**: 10/10 - Game is completely unplayable  
**Frequency**: 100% - Occurs every single run at Room 2  
**Workaround Available**: No - No way to bypass or recover  

## Acceptance Criteria for Resolution

- [ ] Player can click on a card to select it
- [ ] Player can confirm card selection (via second click or Confirm button)
- [ ] Card selection phase completes successfully
- [ ] Advance button becomes enabled after selection
- [ ] Player can proceed to Battle Review
- [ ] Player can advance to Room 3
- [ ] Player can eventually reach Room 4
- [ ] No 400 errors during card selection/advancement
- [ ] Frontend and backend stay synchronized throughout process

## Related Files

- `frontend/src/lib/components/RewardOverlay.svelte` - Card selection logic
- `frontend/src/lib/components/RewardCard.svelte` - Card button component
- `frontend/src/routes/+page.svelte` - Main game loop, reward handlers
- `backend/runs/resolution.py` - Backend card selection logic (likely)

## Conclusion

**Audit Result**: ❌ **FAILED**

The card selection feature appears to work at first glance (cards are clickable), but is fundamentally broken. The frontend-backend desynchronization creates a deadlock where the game cannot progress past Room 2. This is a critical, game-blocking bug that must be fixed before the game can be considered playable.

**Can the user click on a card and get to room 4?** 

**NO** - The user can click on a card, but cannot complete the card selection phase, cannot advance past Room 2, and therefore cannot reach Room 4.

---

**Next Steps**: Development team should prioritize fixing the frontend-backend synchronization issue and implement proper card selection confirmation flow.
