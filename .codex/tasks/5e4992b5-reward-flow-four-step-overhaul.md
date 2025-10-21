# Rebuild reward overlay into four-phase flow

## Summary
Umbrella pointer for the reward overlay overhaul. The monolithic work item has been decomposed into focused umbrellas, each of which now references bite-sized implementation tasks so coders can land the Drops → Cards → Relics → Review experience incrementally.

## Subtasks
- `.codex/tasks/1b801b74-reward-overlay-step-controller.md` — controller umbrella.
  - `.codex/tasks/f7ae6ddd-reward-overlay-state-machine.md`
  - `.codex/tasks/01508135-drops-phase-overlay-refactor.md`
  - `.codex/tasks/bcfc52bc-reward-advance-countdown.md`
  - `.codex/tasks/6afb12ae-reward-overlay-resilience.md`
- `.codex/tasks/b500ea24-card-relic-confirmation-refresh.md` — card/relic UX umbrella.
  - `.codex/tasks/ebfb0389-card-highlight-wiggle.md`
  - `.codex/tasks/d7196ce9-relic-highlight-confirm.md`
  - `.codex/tasks/1f2b8b4a-reward-confirm-accessibility.md`
- `.codex/tasks/1f113358-reward-automation-doc-sync.md` — automation + docs umbrella.
  - `.codex/tasks/68168a61-reward-automation-advance-hooks.md`
  - `.codex/tasks/b8904271-reward-regression-coverage.md`
  - `.codex/tasks/2d6e3f12-reward-overlay-docs-update.md`

## Notes
- Use this parent file to coordinate sequencing and cross-task dependencies.
- Revisit once all subtasks close to confirm no follow-up umbrella work remains.

## Audit Findings (2025-10-21)

**Status:** ❌ **BLOCKING ISSUES FOUND** - Task is NOT ready for review

**Severity:** CRITICAL - Reward flow is completely non-functional

### Critical Issue: Infinite Error Loop Blocking All Progression

During playtest at pressure 0, the reward overlay becomes stuck in the Drops phase and cannot progress to Cards phase. Symptoms:
- After winning first battle, Drops phase renders correctly showing loot
- "Advance" button appears active with "Advance ready." status
- Frontend repeatedly attempts to acknowledge loot via `/api/rewards/loot/{run_id}` 
- Backend returns HTTP 400: "not awaiting loot" (reward_service.py:281)
- Error overlay appears: "Cannot advance room until all rewards are collected"
- Cycle repeats indefinitely every ~10 seconds - player is completely stuck

**Root Cause:** Frontend reward flow controller and backend reward state are out of sync. The backend `awaiting_loot` flag is `False` when frontend expects it to be `True`, preventing loot acknowledgement.

**Impact:** 
- Complete gameplay blocker - players cannot progress beyond first battle
- Entire reward system non-functional
- Cannot test Cards, Relics, or Battle Review phases
- All 12 subtasks marked "ready for review" cannot be validated

**Evidence:** Screenshot at https://github.com/user-attachments/assets/1e9ceefa-b77c-4132-b9aa-efa590ed8958

### Additional Issues Found:

1. **Phase count discrepancy:** Task specifies 4 phases (Drops/Cards/Relics/Review) but UI shows only 3 phases (Drops/Cards/Battle Review). Relics phase missing from numbered sequence.

2. **All subtasks falsely marked "ready for review":** Despite fundamental reward flow being broken, all 12 subtasks claim completion. Integration testing was clearly insufficient.

3. **Documentation inaccuracy:** `frontend/.codex/implementation/reward-overlay.md` describes functional behavior that does not work in practice.

### Required Actions Before Review:

**CRITICAL (P0):**
- [ ] Fix backend/frontend state synchronization issue
- [ ] Enable successful Drops → Cards transition
- [ ] Replace infinite retry loop with graceful error recovery
- [ ] Test complete flow through all phases

**HIGH (P1):**
- [ ] Clarify and fix 3-phase vs 4-phase discrepancy
- [ ] Remove "ready for review" from all 12 subtasks until functional
- [ ] Add integration tests validating full reward flow
- [ ] Update documentation to match actual behavior

**Playtest Results:** 
- Target: 6 rooms at pressure 0
- Actual: 1 room completed (stuck in reward phase, unable to progress)
- Result: **FAILED** - Critical blocker prevents gameplay

### Audit Report:

See detailed analysis in `.codex/audit/5ab6729c-reward-flow-four-step-overhaul-audit.md`

**Auditor's Summary:** The reward flow overhaul requires significant debugging and fixing before it can be reviewed. While UI components appear visually complete, the core state management is fundamentally broken. Recommend blocking all related work until state sync issue is resolved and end-to-end testing passes.

**Next Steps:** Development team should address the `awaiting_loot` state sync issue as highest priority, then conduct full integration testing before re-submitting for review.

---

**more work needed** — Audit found critical state sync bug causing infinite error loop in Drops phase. Backend `awaiting_loot` flag mismatch prevents progression. See `.codex/audit/5ab6729c-reward-flow-four-step-overhaul-audit.md` for full analysis.
