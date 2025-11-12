# Task: Restore Boss-Tier Passive Coverage

## Background
The boss passive directory mirrors the normal roster names but every module is a stub. For instance,
`backend/plugins/passives/boss/kboshi_flux_cycle.py` contains only a comment and `pass` (lines 1-3), so the loader cannot
produce boss-specific passives even though the naming scheme implies they should exist. The gap forced us to cram boss rules
into the normal passives (Luna Midori’s `Lunar Reservoir` checks for `"boss"` directly), which muddies the tier boundaries and
prevents reuse when new foes are built.

## Problem
Boss encounters currently fall back to normal passives or fail to load because there is no boss-tier implementation. This prevents
us from giving bosses the enhanced behaviours their data files expect and risks runtime errors if we ever reference a boss passive ID.
It also means every character file has to remember to special-case things like `"glitched boss"` or `"prime boss"` inside its default
passive, exactly the tight coupling we are trying to eliminate.

## Requested Changes
- Audit `backend/plugins/passives/boss/` and replace each placeholder with an actual passive implementation. Reuse the normal logic
  when appropriate but adjust stats, triggers, and stack caps to match boss balance goals.
- Add defensive logic so that bosses gracefully clean up event subscriptions on defeat/battle end (mirroring the patterns used in the
  normal passives).
- Extend the passive registry tests to assert that every boss file registers a class and that instantiation works without raising.
- Encode the boss-tier differences directly in each plugin's `about`/`describe()` output so UI copy and logs communicate the upgraded behaviour.
- As part of the rollout, remove hard-coded `"boss"` branches from the normal passives (Luna’s reservoir, etc.) and ensure each
  character’s boss behaviour lives exclusively in `backend/plugins/passives/boss/<character>.py`.
- Keep each boss passive on the original character’s theme: lean into their kit, personality, and resource hooks so the boss tier
  feels like a climactic expression of that character rather than an arbitrary stat stick.

## Acceptance Criteria
- Every module in `backend/plugins/passives/boss/` defines at least one concrete passive class with `plugin_type = "passive"`.
- Passive discovery reports boss IDs, and smoke tests confirm they can be instantiated and triggered.
- Battle simulations (unit or integration tests) verify representative boss passives execute their intended effects.
- Plugin metadata documents the presence and purpose of the boss-specific passives.
- Normal-tier passives no longer contain boss-only escape hatches once their boss variant exists.
