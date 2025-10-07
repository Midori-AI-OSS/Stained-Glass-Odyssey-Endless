# Rank Badge Status

The dedicated rank badge overlay was retired. Fighter portraits now expose rank information via the `data-rank-tag` attribute on `LegacyFighterPortrait.svelte`, and outline effects remain in `BattleFighterCard.svelte` for Prime and Boss designations.

There is no longer a reusable badge component or `rankStyles` mapping to maintain, and the Vitest suite that previously validated badge rendering (`tests/rank-badges.vitest.js`) was removed.
