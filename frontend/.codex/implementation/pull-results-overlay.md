# Pull Results Overlay

`src/lib/components/PullResultsOverlay.svelte` displays gacha pull results.
It accepts a `results` array and uses `CurioChoice.svelte` to render each
entry. Results are queued and revealed one at a time with a simple slide/fade
animation. After all items appear a Done button lets the player close the
overlay.

Audio cues are sourced through `createDealSfx`, a thin wrapper around the
shared `createSequentialSfxPlayer` helper in `systems/sfx.js`. The helper
normalizes the `sfxVolume`, clones active audio nodes so overlapping deal
effects never cut each other off, and resolves clips from the
`'ui/pull/deal'` alias before falling back to the Kenney book-flip effects.
The same SFX utility also exposes the `'ui/reward/drop'` alias for loot drops
so pull and reward overlays share a consistent retry-safe playback path.
