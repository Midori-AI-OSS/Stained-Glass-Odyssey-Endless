# Task: Flesh Out Prime Passive Variants

## Background
Prime-tier characters are supposed to represent the pinnacle builds, yet their passives are missing. Every module in
`backend/plugins/passives/prime/` is just a two-line stub with `pass` (e.g., `backend/plugins/passives/prime/kboshi_flux_cycle.py`
lines 1-3). The passive registry therefore has no prime entries, and any reference to a prime passive ID will fail.

## Problem
Without functional prime passives we cannot deliver the power spike or mechanical twists expected at that tier. The empty modules
also make it ambiguous whether prime passives should exist at all, which blocks design discussions and implementation planning.

## Requested Changes
- Define concrete prime passive classes in each module under `backend/plugins/passives/prime/`. Start from the normal versions but
  document and implement the upgrades that justify the prime tier (stronger effects, additional triggers, etc.).
- Ensure the new classes expose meaningful `describe()`/`get_description()` output so the UI can explain the enhancements.
- Add automated coverage (unit tests or snapshot checks) verifying that prime passives load through `PassiveRegistry` and apply their
  special rules without raising.
- Document the upgrades directly in each plugin's `about`/`describe()` output so the UI and inventory surface the differences without extra `.codex` updates.

## Acceptance Criteria
- The prime passive directory no longer contains raw placeholders; each file provides a usable passive class.
- Loading the passive registry includes prime IDs, and tests confirm they can be instantiated and invoked.
- Prime passives demonstrate tier-appropriate enhancements compared to their normal counterparts.
- Plugin metadata (`about` strings or `describe()` output) clearly conveys the intent and behaviour of the prime-tier passives.
