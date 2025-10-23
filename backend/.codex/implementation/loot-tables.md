# Loot Tables

Battle rewards include gold, relic choices, upgrade items, and pull tickets. Gold
and item drops scale with room difficulty and the party's rare drop rate (`rdr`).

## Gold
- **Normal battles:** `5 × loop × rand(1.01–1.25)`
- **Boss battles:** `20 × loop × rand(1.53–2.25)`
- **Floor bosses:** `200 × loop × rand(2.05–4.25)`

The result is multiplied by `rdr` before being added to the party. The same
amount is emitted on the `gold_earned` event so relics can modify the final
reward.

## Relics
- **Normal battles:** `10% × rdr` chance for a relic (70% 1★, 20% 2★, 10% 3★)
- **Boss or floor bosses:** `50% × rdr` chance for a relic (60% 3★, 30% 4★, 10% 5★)

`rdr` scales the drop chance and, at very high values, can roll to upgrade relic
star rank. Every additional star requires 1000× more `rdr` than the last:
moving from 3★ to 4★ takes 1000% `rdr`, and 5★ demands 1,000,000%, but even at
those values success isn't guaranteed.

## Upgrade Items
- **Normal battles:** 1–2★ items
- **Boss battles:** 1–3★ items
- **Floor bosses:** 3–4★ items

The band determines the maximum star rank; the minimum starts at the lower
value and rises with floor, loop count, and Pressure. Results are capped at 4★
and use the foe's element at random.

Rare drop rate now upgrades item stars in single steps driven by orders of
magnitude. We take `log10(max(rdr, 1.0))`, round down, and apply that many
sequential +1 star bumps (10× → +1★, 100× → +2★, 1000× → +3★), clamping the
result at 4★. For example, an item that rolls 2★ with 1,500% `rdr` gains three
bumps and emerges as a 4★ reward.

Any leftover multiplier after removing those full 10× steps is converted into at
most one consolation item. The remainder (between 1× and <10×) maps to a
probability `(residual - 1) / 9` for a second drop sharing the first item's
element at its baseline star rank. That means even extreme `rdr` values still
produce at most two upgrade items while providing a smooth curve for partial
bonuses.

If auto-crafting is enabled, 125 lower-star items combine into the next tier up
to 4★, and sets of ten 4★ items convert into a gacha ticket. `rdr` now
influences both the upgrade item star bumping described above and the chance for
that optional consolation drop.

## Pull Tickets
- **Normal battles:** `0.05% × rdr` chance
- **Boss-strength battles:** `min(5% × rdr, 100%)` chance (applies when strength > 1.0)
- **Floor bosses:** Guaranteed pull ticket drop

These tickets drop alongside the other rewards listed above.

## RDR Effects
`rdr` multiplies gold rewards, upgrade item counts, relic drop odds, and pull
ticket chances. It can also raise item, relic, and card star ranks when `rdr`
is extraordinarily high: items use the single-step `log10` upgrade rule above,
while relics and cards continue to follow their existing high-threshold rolls
for extra stars (3★→4★ at 1000%, 4★→5★ at 1,000,000%).

Top-tier drops may award 5★ cards like Phantom Ally, Temporal Shield, or
Reality Split, each capable of dramatically altering battle flow.
