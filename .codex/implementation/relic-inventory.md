# Relic Inventory

`RelicInventory.svelte` uses `MenuPanel` to show a grid of relic names. If no
relics are held, the menu reports an empty inventory. The inventory can be
accessed during combat to review collected relics and their effects. Upgrade
materials now appear alongside cards and relics in `InventoryPanel.svelte`,
rendered in a color‑coded grid with quantity badges and a detail pane.

Relic entries display their stack count and expose their description as tooltip
text via the `about` field returned by the backend.

## Implemented Relics
- 1★ Rusty Buckle – All allies bleed for 5% Max HP per stack at the start of each turn. When the party loses HP equal to 50× (5000%) of its total Max HP per stack (adding another 10× / 1000% for each additional stack), it fires 5 Aftertaste hits plus 3 per extra stack, each hit equal to 0.5% of the total HP lost.
- 1★ Threadbare Cloak – Allies start battle with a shield equal to 3% Max HP per stack.
- 1★ Lucky Button – +3% Crit Rate; missed crits add +3% Crit Rate next turn.
 - 1★ Bent Dagger – +3% ATK; when a foe dies, allies gain +1% ATK for the rest of combat.
- 1★ Old Coin – +3% gold earned; first shop purchase refunded 3% of cost.
 - 1★ Shiny Pebble – +3% DEF per stack; the first time an ally is hit they gain +3% mitigation per stack for 1 turn.
 - 1★ Herbal Charm – Heals party members for 0.5% Max HP at the start of each turn.
 - 1★ Tattered Flag – +3% party Max HP; when an ally falls, survivors gain +3% ATK.
- 1★ Wooden Idol – +3% Effect Res; resisting a debuff grants +1% Effect Res next turn.
- 1★ Pocket Manual – +3% ATK; every 10th hit deals an extra 3% damage.
- 2★ Vengeful Pendant – Reflects 15% of damage taken back to the attacker.
- 2★ Arcane Flask – After an Ultimate, grant a shield equal to 20% Max HP per stack.
- 2★ Echo Bell – First action each battle repeats at 15% power per stack.
- 2★ Frost Sigil – Hits apply chill dealing 5% ATK as Aftertaste per stack.
- 2★ Ember Stone – Below 25% HP, allies burn their attacker for 50% ATK.
- 2★ Guardian Charm – Lowest-HP ally gains +20% DEF at battle start.
- 2★ Killer Instinct – Ultimates grant +75% ATK for the turn; killing blows upgrade that bonus into +50% SPD for two turns per stack.
- 3★ Greed Engine – Party loses 1% HP per turn, gains +50% gold, and raises rare drop rate by 0.5% plus 0.1% per extra stack.
- 3★ Stellar Compass – Critical hits grant permanent +1.5% ATK and gold rate.
- 3★ Echoing Drum – First attack each battle repeats at 25% power.
- 4★ Null Lantern – Removes shops; fights drop additional pulls.
- 4★ Traveler's Charm – When hit, gain +25% DEF and +10% mitigation next turn per stack.
- 4★ Timekeeper's Hourglass – Each turn, 10% base chance (+1% per additional stack) for ready allies to gain a 2-turn +20% SPD buff per stack.
- 5★ Paradox Hourglass – 60% chance to sacrifice up to one ally per stack (max 4); survivors gain huge stat multipliers and foes lose defense.
- 5★ Soul Prism – After battles, revives fallen allies at 1% HP, applies a stack-scaling Max HP penalty (75% minus 5% per extra stack), and grants +5% DEF/+5% mitigation plus +2% per additional stack.
- 5★ Omega Core – Multiplies all stats by 6x plus 1x per stack for 10 turns +2 per stack before draining escalating HP.

## Testing
- `bun test`
