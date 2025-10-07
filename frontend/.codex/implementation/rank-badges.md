# Rank Badge Implementation

Rank badges are rendered by `src/lib/battle/RankBadge.svelte`. The component consumes a rank string and maps it through `rankStyles.js` to produce a themed overlay that can be reused anywhere a fighter portrait is rendered.

## Rank Mapping

`rankStyles.js` normalises backend rank strings to the following presets:

| Backend Rank        | Tier      | Icon | Notes |
|---------------------|-----------|------|-------|
| `prime`             | Silver    | ★    | Standard Prime foes |
| `glitched prime`    | Gold      | ★    | Adds the animated glitch halo |
| `boss`              | Platinum  | ♛    | Laurel-inspired glyph |
| `glitched boss`     | Diamond   | ◆    | Platinum styling plus glitch halo |

Unknown ranks fall back to a bronze star with a short, auto-generated label. Common ranks such as `normal` are ignored so they do not clutter the UI.

## Component Behaviour

- The badge renders as a circular overlay with `role="img"` and an accessible `aria-label`.
- Glitched ranks layer the provided glitch animation colours on top of the icon, inspired by the CSS reference shared with the task request.
- `size` and `className` props allow parents to anchor the badge wherever they need it; both fighter cards and review portraits position it in the upper-left corner.
- Styling tokens (`data-rank`, `data-rank-tier`, `is-glitched`) are exposed so tests and future stylesheets can key off the active rank.

## Integration Points

- `BattleFighterCard.svelte` keeps the in-battle presentation lightweight, relying on the `rank-prime` / `rank-boss` outline classes for elevated foes instead of rendering a badge.
- `LegacyFighterPortrait.svelte` accepts a `rankTag` override so review tabs can show badges even when tab labels omit the rank text.
- `BattleReview.svelte` stores the foe rank alongside tab metadata and forwards it into `LegacyFighterPortrait` for both the icon column and the detailed breakdown portrait.

## Tests

`tests/rank-badges.vitest.js` verifies two layers:

1. `BattleFighterCard` applies the correct outline classes for Prime and Boss variants without re-introducing badges.
2. `RankBadge.svelte` still renders the correct data attributes and glitch animation for Prime, Glitched Prime, and Boss ranks.

The suite runs via Vitest (`bun x vitest run --config vitest.config.js`) and relies on lightweight mocks for `assetLoader`.
