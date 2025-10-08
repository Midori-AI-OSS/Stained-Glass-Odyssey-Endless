# Summon Manager

The summon manager centralizes all logic for detecting, normalizing, and tracking summons that appear in battle snapshots.  It
wraps the behaviors that previously lived inside `BattleView.svelte` so that multiple components can share a single definition
of what constitutes a summon and how summon metadata is derived.

## Responsibilities

- **Normalization** – converts the variety of snapshot shapes (`array` or keyed `object`) into maps of `owner_id -> summons[]`
  while ensuring each summon carries HP tracking keys, render keys, anchor aliases, and normalized elements.
- **Lifecycle tracking** – keeps a persistent render-key pool per summon signature so summons keep a stable key even when
  snapshots omit explicit IDs, and exposes a `reset()` hook used when a new battle is loaded.
- **HP bookkeeping** – calls the provided `trackHp` callback whenever a summon is prepared so the HP drains history stays in sync
  with the rest of the battle UI.
- **New summon events** – deduplicates summons via `instance_id`/`id` and calls the optional `onNewSummon` callback exactly once
  per previously unseen summon, enabling `BattleView` to queue summon VFX without reimplementing the checks.
- **Shared helpers** – exports `isSummon`, `filterPartyEntities`, and `getSummonIdentifier` so other modules (e.g. overlay views,
  party seed logic) never drift from the canonical summon definition.

## API

```js
import { createSummonManager } from '$lib/systems/summonManager.js';

const summonManager = createSummonManager({
  combatantKey,                 // (kind, id, ownerId) => string used for HP tracking
  resolveEntityElement,         // (summon) => normalized element id (defaults to 'generic')
  applyLunaSwordVisuals,        // (summon, ownerId, baseElement) => summon with Luna Sword visuals applied
  normalizeOwnerId,             // (value) => stable owner identifier string
});

const { partySummons, foeSummons, partySummonIds, foeSummonIds } = summonManager.processSnapshot(snapshot, {
  trackHp: (hpKey, hp, maxHp) => { /* update HP history */ },
  onNewSummon: ({ side, ownerId, summon }) => { /* queue summon effect */ },
});

// Reset between battles
summonManager.reset();
```

The returned maps are keyed by the owning combatant ID and contain fully prepared summon entries.  `partySummonIds` and
`foeSummonIds` expose the identifier sets used by `BattleView` to avoid duplicating summons in the primary party/foe arrays.

Helper exports:

- `isSummon(entity)` – canonical check used across the UI.
- `filterPartyEntities(list)` – strips summons from arbitrary party lists (used by the review overlay).
- `getSummonIdentifier(summon)` – exposes the identifier derivation for tooling/tests.

## Integration Points

- **`BattleView.svelte`** instantiates a manager with battle-specific helpers.  `fetchSnapshot` now delegates summon preparation
  to the manager, relies on `processSnapshot` for deduplication, and resets the manager when the run changes.
- **`OverlayHost.svelte`** imports `filterPartyEntities` to keep the battle review overlay aligned with the battle view’s summon
  definition.
- **`partySeed.js`** imports `isSummon` to skip summons when deriving seed party IDs.
- **Vitest coverage** – see `frontend/tests/summonManager.test.js` for scenarios covering normalization, deduplication, and render
  key persistence.

When extending summon behavior, update the manager so every consumer automatically receives the new logic.
