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
and use the foe's element at random. Each battle drops at least one item by default and
multiplies that quantity by the party's rare drop rate (`rdr`). Fractional results
have a matching chance to award one extra item.

If auto-crafting is enabled, 125 lower-star items combine into the next tier up
to 4★, and sets of ten 4★ items convert into a gacha ticket. `rdr` only affects
how many items appear—it never upgrades their star level.

## Pull Tickets
- **Normal battles:** `0.05% × rdr` chance
- **Boss-strength battles:** `min(5% × rdr, 100%)` chance (applies when strength > 1.0)
- **Floor bosses:** Guaranteed pull ticket drop

These tickets drop alongside the other rewards listed above.

## RDR Effects
`rdr` multiplies gold rewards, upgrade item counts, relic drop odds, and pull
ticket chances. It can also roll to raise relic and card star ranks when `rdr`
is extraordinarily high (3★→4★ at 1000%, 4★→5★ at 1,000,000%) but never
upgrades item stars.

Top-tier drops may award 5★ cards like Phantom Ally, Temporal Shield, or
Reality Split, each capable of dramatically altering battle flow.
