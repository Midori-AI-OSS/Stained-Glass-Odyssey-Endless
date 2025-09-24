# Battle Status & Ambient Effects

`+page.svelte` normalizes battle snapshots so each fighter carries
`passives`, `dots`, and `hots` as arrays of objects. Each effect object
includes an `id`, optional `name`, `stacks`, `turns`, and `source` along
with `damage` or `healing` values. `StatusIcons.svelte` and
`FighterPortrait.svelte` consume these arrays to render icons with stack
counts and tooltips showing effect details. `FighterUIItem.svelte`
renders passive stack indicators beside the element chip. Each passive
descriptor exposes a `display` hint:

- `spinner` passives show an animated spinner.
- `pips` render up to five filled pips, switching to a numeric count when stacks exceed five.
- `number` renders the stack count, or `count/max` when a maximum applies.

CombatViewer lists passive effects and applies the same display hints within its status panels.

These indicators respect Reduced Motion settings and expose
tooltips for screen readers and mouse users. When a fighter's ultimate
becomes ready, an element-colored pulse briefly radiates from the
ultimate ring in `FighterPortrait`; portraits also gain a soft element
halo around the artwork. Both effects are skipped when Reduced Motion is
enabled. The ultimate gauge in `FighterUIItem` now slides its fill and
feathered edge with a 0.3s ease-out transition while charging. The fill
also slowly tilts left and right, the sway intensifying up to a
one-degree angle around 98% charge. Reduced Motion disables both the
transition and the tilt.

When a fighter's element changes mid-battle, the portrait outline and
ultimate icon briefly flash using the `element-change` animation. The
update transitions the element color and icon smoothly and is skipped
when Reduced Motion is enabled.

HP bars for party members, foes, and their summons animate their fill widths
and overheal overlays with short transitions. When Reduced Motion is enabled,
these transitions are removed for instant updates.

## Battle Music Metadata

The `/players` bootstrap payload now includes a `music.weights` object for each
character. The map provides playlist weighting hints for the `normal`, `weak`,
and `boss` encounter categories and always surfaces a `default` multiplier.
Frontend helpers read these weights when constructing battle playlists so
special cases like Luna's themed tracks are provided by backend metadata rather
than hard-coded in the UI. When metadata is missing or invalid, the selector
falls back to a neutral weight of `1` for all categories and relies on the
fallback library when no character playlists are available (which also covers
reduced-motion safe playback).

## Stained-Glass Palette

Effect indicators and bar graphs should reflect the project's stained-glass
aesthetic. Use vibrant, glass-like hues for these elements, drawing inspiration
from the element palette returned by `getElementBarColor` in
`frontend/src/lib/BattleReview.svelte`.

## Enrage Indicator Redesign

The previous blue/red full‑screen flashing during enrage has been replaced
with an ambient orbs effect implemented in `battle/EnrageIndicator.svelte`:

- Orbs gently drift and hue‑shift across the battlefield while combat is
  active and fade out smoothly once rewards appear (2–3s despawn).
- The indicator is now driven by `active` (combat state) rather than a binary
  enrage flag to avoid abrupt start/stop artifacts.
- Reduced Motion is respected: animations are disabled and a calm static
  ambience remains visible.

## Animation Pipeline

`BattleEffects.svelte` is currently disabled (no‑op) behind an internal
feature flag while we stabilize the runtime integration. When enabled, it
wraps the `@zaniar/effekseer-webgl-wasm` runtime. It creates a full-screen
canvas, initializes the WebGL context, and loads `.efkefc` files from
`src/lib/assets/effects`. `BattleView.svelte`
watches incoming battle log lines, maps keywords like `damage`, `burn`,
`poison`, and `heal` to effect names, and passes the result to the
component so the matching animation plays. `vite.config.js` copies the
`effekseer.wasm` runtime and marks `.efkefc` files as static assets so the
player can fetch them at runtime.

`BattleEventFloaters.svelte` listens to the incremental `recent_events`
stream from battle snapshots. It filters damage and healing payloads,
derives damage-type visuals through `assetLoader.js`, and spawns floating
badges that drift upward over the polling cadence. The overlay removes each
badge after its animation (or a timer when Reduced Motion is enabled) so
the DOM stays bounded.
