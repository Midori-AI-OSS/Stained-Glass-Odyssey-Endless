# Gacha system

## Presentation flow
- Determine the highest rarity in the pull results.
- Play the video or animation for that rarity unless the player skips.
- After the animation (or immediately if skipped), show a results menu.
  - Single pulls show one item.
  - Multi pulls list all items.
- Allow skipping at any point to jump directly to the results menu.

Adds a basic character pull system seeded from `plugins/characters`.
Player plugins declare a `gacha_rarity` (5★ or 6★), and the manager builds
its pools dynamically so new recruits become pullable without code changes.

## Features
- 1, 5, or 10 pulls at a time.
- Each pull consumes one ticket; the server rejects requests when tickets are insufficient.
- Failed pulls grant element-specific upgrade items. Roll table: 1★ 10%, 2★ 50%,
  3★ 30%, 4★ 10%. Higher pity shifts these odds toward rarer items.
 - The pulls menu disables pull buttons when available tickets are below the selected count.
- Upgrade items auto-craft within their element (125 lower-star items
  form one higher star) and 4★ items remain at that tier. Auto-crafting is
  always active and no manual toggle or ticket conversion is available.
- 5★ characters become available as pity rises from 0.001% to ~5% at pull 159, guaranteeing a 5★ at 180. 6★ characters roll independently at a flat 0.01% chance.
- Duplicate characters apply Vitality and stat bonuses. Each stat uses the first
  duplicate's value from the player plugin and increases by 5% per additional
  stack. Characters can stack duplicates endlessly; each extra pull increases
  the stack and grants the corresponding bonuses.
- Ownership data serializes to JSON for persistence.
- `GachaManager` stores pity counters, upgrade item totals, and character stack
  counts in the encrypted save database and exposes Quart endpoints for pulls
  and state queries.
