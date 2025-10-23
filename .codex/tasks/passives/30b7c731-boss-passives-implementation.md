# Task: Restore Boss-Tier Passive Coverage

## Background
The boss passive directory mirrors the normal roster names but every module is a stub. For instance,
`backend/plugins/passives/boss/kboshi_flux_cycle.py` contains only a comment and `pass` (lines 1-3), so the loader cannot
produce boss-specific passives even though the naming scheme implies they should exist.

## Problem
Boss encounters currently fall back to normal passives or fail to load because there is no boss-tier implementation. This prevents
us from giving bosses the enhanced behaviours their data files expect and risks runtime errors if we ever reference a boss passive ID.

## Requested Changes
- Audit `backend/plugins/passives/boss/` and replace each placeholder with an actual passive implementation. Reuse the normal logic
  when appropriate but adjust stats, triggers, and stack caps to match boss balance goals.
- Add defensive logic so that bosses gracefully clean up event subscriptions on defeat/battle end (mirroring the patterns used in the
  normal passives).
- Extend the passive registry tests to assert that every boss file registers a class and that instantiation works without raising.
- Update `.codex/docs/character-passives.md` (or add a boss-specific appendix) to describe how the boss passives differ from the
  baseline versions.

## Acceptance Criteria
- Every module in `backend/plugins/passives/boss/` defines at least one concrete passive class with `plugin_type = "passive"`.
- Passive discovery reports boss IDs, and smoke tests confirm they can be instantiated and triggered.
- Battle simulations (unit or integration tests) verify representative boss passives execute their intended effects.
- Documentation captures the presence and purpose of the boss-specific passives.
