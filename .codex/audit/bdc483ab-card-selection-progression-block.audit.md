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
   - **Intended Design**: Two-click pattern - first click selects (card wiggles), second click on same card confirms
   - **Current Issue**: The "Advance" button remains disabled indefinitely even after clicking the card twice
   - Message displays: "Advance locked until this phase is complete"
   - The two-click confirmation mechanism is not completing successfully

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

#### Expected Behavior (Design Intent)

1. Click a card once to select it (card should wiggle to indicate selection)
2. Click the same card again to confirm the selection (two-click pattern)
3. Card selection phase completes successfully
4. Advance button becomes enabled (or could act as fallback confirm when card is wiggling)
5. Player can proceed to Battle Review phase
6. Player can advance to Room 3

#### Actual Behavior

- Card selection UI shows but cannot be completed
- Advance button never enables
- Player is permanently stuck at Room 2
- Cannot progress to Room 3 or Room 4
- Game becomes unplayable

### Issue #2: Two-Click Pattern Implementation is Broken

**Severity**: CRITICAL  
**Impact**: The intended two-click confirmation pattern doesn't complete the card selection

**Design Intent**: The code in `RewardOverlay.svelte` (lines 897-918) implements a two-click pattern where:
1. First click highlights/selects the card (card wiggles)
2. Second click on the same card confirms the selection

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

**Current Problems**:
- The two-click pattern is correctly implemented in the code
- However, `performRewardSelection()` is being called but not completing successfully
- The card selection phase never transitions to complete state
- The Advance button never enables after the second click

**Potential Fallback Solution** (as suggested):
- When a card is wiggling (selected but not confirmed), enable the Advance button
- Clicking Advance would confirm the currently wiggling card/relic
- This provides an alternative confirmation method beyond the two-click pattern

### Issue #3: Backend Auto-Selection Bug

**Severity**: CRITICAL  
**Impact**: Backend is incorrectly auto-selecting all cards instead of waiting for user input

**Bug**: The backend automatically selects ALL cards without waiting for user input:

```
INFO Card selection complete: 3 cards selected after 3 attempts
INFO Selected cards: ['guiding_compass', 'vital_core', 'lightweight_boots']
```

**Design Intent Clarification**:
- Backend should **NOT** auto-select cards
- Backend should wait for frontend to send the user's card selection via API call
- Only the user's chosen card should be selected, not all available cards

**Impact**:
- Frontend shows card selection UI and waits for user to choose
- Backend has already selected all cards automatically
- Frontend's selection attempt conflicts with backend's auto-selection
- This creates the deadlock preventing progression

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

1. **Fix Backend Auto-Selection Bug**: Backend must NOT auto-select all cards; it should wait for the frontend API call with the user's chosen card
2. **Fix Two-Click Confirmation Flow**: Ensure `performRewardSelection()` completes successfully when called on the second click
3. **Fix Advance Button State**: Ensure Advance button enables after card selection completes successfully

### Short-Term (High Priority)

4. **Implement Fallback Advance Button**: When a card is wiggling (selected but not confirmed), enable the Advance button to act as a confirmation option
5. **Improve Visual Feedback**: Ensure the card wiggle animation clearly indicates a card is selected and awaiting confirmation
6. **Error Handling**: Handle the HTTP 400 error gracefully with user-friendly message and recovery option

### Long-Term (Medium Priority)

7. **Add Keyboard Support**: Allow Enter key to confirm the currently selected (wiggling) card
8. **Add Skip Option**: Allow players to skip card rewards if desired
9. **Add Testing**: Create automated tests for the two-click card selection flow
10. **Improve Discoverability**: Consider adding a subtle hint that cards require two clicks to confirm (e.g., tooltip or help text)

## Impact Assessment

**User Impact**: 10/10 - Game is completely unplayable  
**Frequency**: 100% - Occurs every single run at Room 2  
**Workaround Available**: No - No way to bypass or recover  

## Acceptance Criteria for Resolution

- [ ] Player can click on a card to select it (first click - card wiggles)
- [ ] Player can confirm card selection via second click on the same card
- [ ] Alternatively, Advance button enables when card is wiggling and can confirm the selection
- [ ] Backend waits for frontend API call instead of auto-selecting all cards
- [ ] Card selection phase completes successfully after user confirmation
- [ ] Advance button becomes enabled after card selection completes
- [ ] Player can proceed to Battle Review phase
- [ ] Player can advance to Room 3
- [ ] Player can eventually reach Room 4
- [ ] No HTTP 400 errors during card selection/advancement
- [ ] Frontend and backend stay synchronized throughout the process

## Related Files

- `frontend/src/lib/components/RewardOverlay.svelte` - Card selection logic
- `frontend/src/lib/components/RewardCard.svelte` - Card button component
- `frontend/src/routes/+page.svelte` - Main game loop, reward handlers
- `backend/runs/resolution.py` - Backend card selection logic (likely)

## Conclusion

**Audit Result**: ❌ **FAILED**

The card selection feature has the correct two-click pattern implemented in the frontend code, but is broken due to two critical issues:

1. **Backend Bug**: Backend auto-selects all cards instead of waiting for the user's choice via API
2. **Frontend Bug**: The two-click confirmation flow (`performRewardSelection()`) doesn't complete successfully

These bugs create a deadlock where the game cannot progress past Room 2. This is a critical, game-blocking bug that must be fixed before the game can be considered playable.

**Can the user click on a card and get to room 4?** 

**NO** - The user can click on a card (first click selects, second click attempts to confirm), but the confirmation doesn't complete, preventing advancement past Room 2 and making Room 4 unreachable.

---

**Next Steps**: 
1. Fix backend to stop auto-selecting cards and wait for frontend API call
2. Debug why `performRewardSelection()` doesn't complete the card selection phase
3. Consider implementing the fallback Advance button confirmation as suggested
