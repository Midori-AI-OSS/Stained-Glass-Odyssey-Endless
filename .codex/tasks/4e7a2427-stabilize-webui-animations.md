Coder, standardize WebUI animation tokens and smooth out battle/menu motion.

## Context
- `frontend/src/lib/components/StarStorm.svelte` (destined to be the `ElementOrbs` backdrop) randomizes orb drift, delays, and colors at module load, leading to inconsistent visuals between renders and no linkage to global animation speed or reduced-motion settings.【F:frontend/src/lib/components/StarStorm.svelte†L1-L120】
- `frontend/src/lib/components/BattleEventFloaters.svelte` hard-codes durations (`BASE_DURATION`, stagger timers) and easing curves with no shared constants, producing abrupt motion compared to other overlays.【F:frontend/src/lib/components/BattleEventFloaters.svelte†L1-L220】【F:frontend/src/lib/components/BattleEventFloaters.svelte†L220-L360】
- `frontend/src/lib/battle/BattleFighterCard.svelte` uses random animation durations/delays for rank outlines and ultimate icon pulses, which makes the UI feel jittery and is difficult to test.【F:frontend/src/lib/battle/BattleFighterCard.svelte†L1-L200】
- Reduced Motion currently only toggles certain transitions off; many components ignore `reducedMotion` props or `prefers-reduced-motion` entirely.

## Requirements
- Create a shared animation token module (e.g., `frontend/src/lib/systems/animationTokens.js`) that defines durations, easings, and opacity curves for primary UI effects (background ambiance, popups, battle floaters, portrait glows).
- Rename `StarStorm.svelte` and the related implementation notes to `ElementOrbs` (or similar) as part of the refactor so the component name matches the current art direction.
- Refactor ElementOrbs, BattleEventFloaters, BattleFighterCard, and other animation-heavy components (e.g., `TripleRingSpinner.svelte`, overlay transitions in `OverlayHost.svelte`) to consume the shared tokens instead of inventing per-file constants/randomization.
- Ensure every component honors the granular motion settings from the new settings tree (see task 16a58b4c) and `window.matchMedia('(prefers-reduced-motion)')` by clamping durations to zero or swapping in static art where appropriate.
- Provide snapshot or unit coverage verifying that animation tokens export the expected structure and that components fall back to static states when motion is disabled.
- Update relevant documentation (`frontend/.codex/implementation/battle-effects.md`, `frontend/.codex/implementation/settings-menu.md`) to describe the token system and how motion flags map to component behavior.

## Notes
- Avoid introducing runtime randomness in animations; if variation is required, derive it deterministically from ids or seeds so renders stay stable between sessions.
- Coordinate with the theme task so token colors/strengths can adapt to the selected theme.

Task ready for implementation.
