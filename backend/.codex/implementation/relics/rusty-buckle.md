# Rusty Buckle Relic Tuning

Rusty Buckle is a tension-building relic that rewards the party for surviving
long engagements. Each stack applies a fixed bleed (5% Max HP per turn) while
tracking how much total Max HP has been lost by the entire party. When the
accumulated loss crosses a threshold the relic unleashes an Aftertaste volley at
random foes.

## HP-loss thresholds
- The threshold multiplier intentionally starts at **50×** party Max HP. Losing
  100 combined HP with a 50× multiplier equates to a 5000% progress bar; the
  volley triggers only after the run has bled out 5000% of the party's Max HP in
  total.
- Additional stacks increase the threshold by **10×** (1000%) each. Two stacks
  therefore require 60×, three stacks 70×, and so on.

These values look extreme if interpreted as conventional percentages, but they
are by design. The high multipliers prevent chip damage from spamming Aftertaste
while still allowing long boss fights to build momentum and eventually detonate
a large volley.

## Player-facing description
The in-game description mirrors the same multiplier (e.g., "Each 5000% party HP
lost…"). This phrasing is intentional and should not be converted to 50%.

## Implementation notes
- `_threshold_multiplier` in `backend/plugins/relics/rusty_buckle.py` returns
  `50.0 + 10.0 * max(stacks - 1, 0)`.
- Comments in the module document the intent so future edits keep the 50× base
  multiplier intact.
