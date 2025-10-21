# Audit Report: Reward Flow Four-Step Overhaul

**Task ID:** 5e4992b5-reward-flow-four-step-overhaul  
**Audit Date:** 2025-10-21  
**Auditor:** GitHub Copilot Coding Agent  
**Status:** **BLOCKING ISSUES FOUND** - Major functionality broken

## Executive Summary

The reward flow four-step overhaul (Drops → Cards → Relics → Battle Review) has been **partially implemented** but contains **critical blocking bugs** that prevent the system from functioning. The playtest at pressure 0 revealed that the reward overlay becomes stuck in the Drops phase and cannot progress, with repeated backend errors creating an infinite error loop.

**Severity:** **CRITICAL** - The reward flow is completely non-functional in its current state.

## Audit Scope

- Parent task: `.codex/tasks/5e4992b5-reward-flow-four-step-overhaul.md`
- All 12 subtask files
- Implementation documentation: `frontend/.codex/implementation/reward-overlay.md`
- Runtime testing: 1 room completed at pressure 0 (unable to complete 6 rooms due to blocking bug)

## Critical Issues Found

### 1. **CRITICAL: Infinite Error Loop in Drops Phase**

**Severity:** Blocking  
**Location:** Reward flow progression, Drops → Cards transition  
**Evidence:** Playtest screenshot at https://github.com/user-attachments/assets/1e9ceefa-b77c-4132-b9aa-efa590ed8958

**Symptoms:**
- After winning a battle, the reward overlay opens showing the Drops phase
- The "Advance" button appears as "active" and shows "Advance ready."
- Frontend logs `[INFO] [rewardTelemetry] {kind: drops-complete...}` every ~10 seconds
- Backend returns HTTP 400 error: "not awaiting loot"
- Error overlay appears: "Cannot advance room until all rewards are collected."
- The cycle repeats indefinitely - user is completely stuck

**Root Cause Analysis:**
The frontend reward flow controller and backend reward state are out of sync:

1. Frontend enters Drops phase and marks it as complete
2. Frontend attempts to acknowledge loot via `/api/rewards/loot/{run_id}`
3. Backend checks `state.get("awaiting_loot")` and finds it `False`
4. Backend raises `ValueError("not awaiting loot")` (reward_service.py:281)
5. Frontend receives 400 error and retries indefinitely
6. User cannot progress past Drops phase

**Code Reference:**
```python
# backend/services/reward_service.py:276-281
async def acknowledge_loot(run_id: str) -> dict[str, Any]:
    lock = reward_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
        state, rooms = await asyncio.to_thread(load_map, run_id)
        if not state.get("awaiting_loot"):
            raise ValueError("not awaiting loot")
```

**Impact:**
- **Complete gameplay blocker** - players cannot progress beyond the first battle
- Reward system is entirely non-functional
- All 12 subtasks claiming "ready for review" are suspect due to this fundamental failure

**Reproduction Steps:**
1. Start a run at pressure 0
2. Win the first battle
3. Observe reward overlay opens to Drops phase
4. Wait for auto-advance or attempt manual advance
5. System enters infinite error loop

### 2. **MAJOR: Discrepancy Between Task Files and Implementation**

**Severity:** High  
**Type:** Documentation/Specification Mismatch

**Issue:** The parent task file references a **four-phase flow** (Drops → Cards → Relics → Review) but the actual implementation and documentation describe **slightly different phases**:

- **Task file states:** "Drops → Cards → Relics → Review"
- **Implementation documentation states:** "Drops → Cards → Relics → Battle Review"
- **Actual UI shows (from playtest):** Only 3 phases in the right rail:
  - 1. Drops
  - 2. Cards  
  - 3. Battle Review
  - **Relics phase is missing from the UI**

**Evidence from Screenshot:**
The "REWARD FLOW" panel shows only three numbered phases, not four. The Relics phase appears to be missing or combined with another phase in the actual implementation.

**Impact:**
- Confusion about actual vs. intended behavior
- Test coverage may be incomplete if phases don't match specs
- Documentation needs reconciliation with actual implementation

### 3. **MAJOR: All Subtasks Marked "ready for review" Despite Broken Functionality**

**Severity:** High  
**Type:** Process/Quality Assurance

**Issue:** All 12 subtask files are marked with `ready for review` footer, yet the fundamental reward flow is completely broken:

**Subtasks claiming completion:**
- `1b801b74-reward-overlay-step-controller.md` - "ready for review"
- `f7ae6ddd-reward-overlay-state-machine.md` - "ready for review"
- `01508135-drops-phase-overlay-refactor.md` - "ready for review" (with auditor note about rail leaking)
- `bcfc52bc-reward-advance-countdown.md` - "ready for review" (with auditor note about rail leaking)
- `6afb12ae-reward-overlay-resilience.md` - "ready for review"
- `b500ea24-card-relic-confirmation-refresh.md` - "ready for review"
- `ebfb0389-card-highlight-wiggle.md` - "ready for review"
- `d7196ce9-relic-highlight-confirm.md` - "ready for review"
- `1f2b8b4a-reward-confirm-accessibility.md` - "ready for review" (shows status update from 2025-02-15)
- `1f113358-reward-automation-doc-sync.md` - "ready for review"
- `68168a61-reward-automation-advance-hooks.md` - "ready for review"
- `b8904271-reward-regression-coverage.md` - "ready for review"
- `2d6e3f12-reward-overlay-docs-update.md` - "ready for review"

**Observations:**
- Two subtasks have "Auditor note" sections mentioning reward rail leaking to home screen (since fixed)
- One subtask shows a status update from "2025-02-15" (future date suggests test data or placeholder)
- Despite all subtasks being marked complete, the basic functionality is completely broken

**Impact:**
- Cannot trust "ready for review" status
- Suggests insufficient integration testing
- Indicates need for stricter review standards before marking tasks complete

### 4. **MODERATE: Missing Relics Phase in Actual UI**

**Severity:** Moderate  
**Type:** Implementation Gap

**Issue:** The task specifications and documentation clearly describe a four-phase flow including Relics, but the playtest shows only three phases in the UI's reward flow panel. The Relics phase may be:
- Skipped when no relics are awarded
- Combined with another phase
- Missing due to incomplete implementation

**Evidence:**
- Parent task: "Drops → Cards → Relics → Review"  
- Actual UI (screenshot): "1. Drops, 2. Cards, 3. Battle Review"
- No "Relics" phase visible in the numbered sequence

**Impact:**
- Cannot validate Relics-related subtasks without seeing the phase
- May indicate that relic tasks are not actually implemented
- Testing coverage incomplete

### 5. **MINOR: Console Warnings During Normal Operation**

**Severity:** Low  
**Type:** Code Quality

**Console messages observed:**
```
[WARNING] [assetRegistry] portrait-fallback
[DEBUG] [BattleView] Unable to canonicalize combatant id {candidate: becca, normalized: becca...
```

While not blocking, these suggest minor code quality issues that should be addressed.

## Compliance with Task Requirements

### Parent Task (5e4992b5) Requirements:
- ✅ Subtask files created (all 12 exist)
- ❌ Functional four-phase flow (completely broken)
- ❌ Drops → Cards → Relics → Review sequence (stuck at Drops, Relics phase not visible)
- ❌ "ready for review" accuracy (falsely marked as complete)

### Subtask Review Status:

| Subtask | File | Status Claim | Actual Status |
|---------|------|--------------|---------------|
| 1b801b74 | reward-overlay-step-controller.md | ready for review | ❌ **BROKEN** - controller doesn't advance |
| f7ae6ddd | reward-overlay-state-machine.md | ready for review | ❌ **BROKEN** - state machine doesn't progress |
| 01508135 | drops-phase-overlay-refactor.md | ready for review | ⚠️ **PARTIAL** - Drops render but can't exit |
| bcfc52bc | reward-advance-countdown.md | ready for review | ❌ **BROKEN** - advance doesn't work |
| 6afb12ae | reward-overlay-resilience.md | ready for review | ❌ **BROKEN** - infinite error loop shows no resilience |
| b500ea24 | card-relic-confirmation-refresh.md | ready for review | ❓ **UNTESTABLE** - can't reach Cards phase |
| ebfb0389 | card-highlight-wiggle.md | ready for review | ❓ **UNTESTABLE** - can't reach Cards phase |
| d7196ce9 | relic-highlight-confirm.md | ready for review | ❓ **UNTESTABLE** - can't reach Relics phase |
| 1f2b8b4a | reward-confirm-accessibility.md | ready for review | ❓ **UNTESTABLE** - can't reach confirm flows |
| 1f113358 | reward-automation-doc-sync.md | ready for review | ❌ **BROKEN** - automation would fail |
| 68168a61 | reward-automation-advance-hooks.md | ready for review | ❌ **BROKEN** - advance hooks don't work |
| b8904271 | reward-regression-coverage.md | ready for review | ❌ **BROKEN** - tests must be failing or incomplete |
| 2d6e3f12 | reward-overlay-docs-update.md | ready for review | ⚠️ **INACCURATE** - docs don't match broken reality |

## Testing Results

### Playtest Summary:
- **Target:** 6 rooms at pressure 0
- **Actual:** 1 room completed (stuck in reward phase, unable to progress)
- **Result:** **FAILED** - Critical blocker prevents gameplay

### What Works:
- ✅ Run setup and configuration
- ✅ Battle system executes correctly
- ✅ Reward overlay opens after battle
- ✅ Drops phase renders with correct items (Light Upgrade, Gold)
- ✅ Right rail "Reward Flow" panel displays
- ✅ Visual styling appears correct (stained-glass design)
- ✅ Advance button renders and shows "active" state
- ✅ Telemetry events fire (`drops-complete`)

### What's Broken:
- ❌ **Cannot progress past Drops phase** (infinite loop)
- ❌ **Backend/frontend state synchronization**
- ❌ **Loot acknowledgement flow**
- ❌ **Error handling creates error storm instead of graceful recovery**
- ❌ **Cannot test Cards, Relics, or Battle Review phases**
- ❌ **Cannot complete a full run**

## Documentation Review

### Implementation Documentation (`frontend/.codex/implementation/reward-overlay.md`):

**Quality:** High (well-written, comprehensive)  
**Accuracy:** Questionable (describes features that don't work)

**Positive Aspects:**
- Detailed explanation of four-phase flow
- Comprehensive coverage of components and data flow
- Clear accessibility notes
- Good manual QA checklist

**Issues:**
- Documentation describes functional behavior that is completely broken in practice
- Manual QA checklist items cannot be validated due to blocking bug
- No warning about known issues or incomplete implementation
- Suggests features are working when they are not

**Recommended QA Checklist Items from Docs (All Failed):**
- ❌ "Trigger a full Drops → Cards → Relics → Review sequence" - **Cannot complete**
- ❌ "Start a countdown in Drops phase, then stage a card" - **Countdown doesn't advance**
- ❌ "Confirm automation hooks log both manual and auto reasons" - **Automation would fail**
- ❌ "Navigate overlay using only keyboard" - **Stuck at Drops, cannot test**
- ❌ "Screen reader announcements" - **Cannot test beyond Drops**

## Recommendations

### Immediate Actions Required:

1. **CRITICAL: Fix Backend/Frontend State Sync**
   - Investigate why `awaiting_loot` is `False` when frontend expects it to be `True`
   - Review `ensure_reward_progression()` and `_update_reward_progression()` logic
   - Add defensive programming to handle state mismatches gracefully
   - **Priority:** P0 - Blocks all other work

2. **CRITICAL: Fix Drops → Cards Transition**
   - Debug the loot acknowledgement flow
   - Ensure state transitions match between frontend controller and backend
   - Add proper error recovery instead of infinite retry loop
   - **Priority:** P0 - Blocks all other work

3. **HIGH: Remove "ready for review" from All Subtasks**
   - All subtasks should be marked as "more work needed" or similar
   - Only mark as "ready for review" after integration testing passes
   - **Priority:** P1 - Prevents false confidence

4. **HIGH: Clarify Phase Count**
   - Reconcile discrepancy between 4-phase spec and 3-phase UI
   - Update all task files and documentation to match actual implementation
   - If Relics should be phase 3, fix the UI; if not, update specs
   - **Priority:** P1 - Required for correct implementation

5. **HIGH: Add Integration Tests**
   - Create end-to-end tests that validate full reward flow
   - Tests should verify each phase transition
   - Tests should catch the state sync issue
   - **Priority:** P1 - Prevent regression

6. **MODERATE: Implement Proper Error Recovery**
   - Replace infinite retry loop with graceful degradation
   - Show actionable error messages to users
   - Log diagnostic information for debugging
   - **Priority:** P2 - Quality of life

7. **MODERATE: Fix Date Inconsistencies**
   - Task `1f2b8b4a` shows status date "2025-02-15" (future date or typo)
   - Review all task files for date accuracy
   - **Priority:** P2 - Documentation hygiene

### Process Improvements:

1. **Require Integration Testing Before "ready for review"**
   - Manual playtesting should be mandatory
   - At minimum: Complete 1 full run through all phases
   - Document test results in task file

2. **Stricter Review Standards**
   - "ready for review" should mean feature works end-to-end
   - Reviewers should verify claims with actual testing
   - Consider requiring screenshot/video evidence

3. **Better State Management Debugging**
   - Add logging for all state transitions
   - Create debug endpoint to inspect reward state
   - Add frontend dev tools for reward flow

## Conclusion

The reward flow four-step overhaul is **NOT READY FOR REVIEW** and should be **BLOCKED** until critical issues are resolved. While significant work has been done on the UI components and documentation, the core functionality is completely broken due to a state synchronization bug between the frontend and backend.

**All 12 subtasks should be re-evaluated** after the critical bugs are fixed, as most cannot be properly tested in the current state.

**The parent task should be marked as "more work needed"** with a clear action plan to:
1. Fix the state sync issue
2. Enable progression through all four phases  
3. Conduct full end-to-end testing
4. Only then mark subtasks as "ready for review"

**Estimated Effort to Fix:** 2-4 hours for an experienced developer familiar with the codebase to debug and fix the state sync issue, plus additional time for comprehensive testing.

---

**Audit Methodology:**
- Reviewed all 12 subtask files
- Reviewed parent task file
- Reviewed implementation documentation
- Attempted playtest of 6 rooms at pressure 0
- Analyzed console logs and error messages
- Reviewed backend code (`reward_service.py`)
- Captured screenshot evidence of broken state

**Next Steps:**
1. Share this audit report with the Task Master
2. Update parent task file to reflect blocking status
3. Do NOT update individual subtasks (per audit instructions)
4. Wait for development team to address critical issues before re-auditing
