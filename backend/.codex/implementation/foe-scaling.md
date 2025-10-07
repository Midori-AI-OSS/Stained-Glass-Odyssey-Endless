# Foe scaling overview

`FoeFactory.scale_stats()` applies several stages when preparing an encounter foe.

1. **Base debuff** – Foes start with the `foe_base_debuff` multiplier applied to
   max HP and attack. Defense receives a smaller multiplier that scales with the
   current floor to keep early battles approachable.
2. **Room scaling** – The configured growth curves and pressure multipliers are
   applied through permanent stat adjustments so the baseline grows alongside the
   run progression.
3. **Threshold enforcement** – Final clamps prevent edge cases such as very low
   defense or HP rolls and synchronize `hp` with the updated `max_hp`.

The spawn debuff now updates the stored baselines before later safeguards run, so
foes retain their intended debuffed HP/ATK/DEF values instead of snapping back to
pre-debuff stats.
