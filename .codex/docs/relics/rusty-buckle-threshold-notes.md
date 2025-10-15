# Rusty Buckle Threshold Rationale

> This design note now lives alongside the other relic references under
> `.codex/docs/relics/` so contributors can locate it with the rest of the relic
> documentation.

Rusty Buckle is tuned to behave like a pressure valve for extremely long
encounters rather than a frequent burst effect. Its charge threshold is
deliberately exaggerated so that chip damage cannot trigger Aftertaste loops by
accident.

- **HP-loss requirement:** Each stack requires the party to lose 50× (5000%) of
  its combined Max HP before a volley fires. Additional stacks add another 10×
  (1000%) per stack.
- **Design intent:** The inflated multiplier lets marathon fights eventually
  erupt into massive Aftertaste barrages without invalidating healing-focused
  strategies in shorter encounters.
- **Player messaging:** The description text reports the same multiplier so the
  UI stays consistent with the underlying math.

Documenting the 5000% baseline prevents future contributors from "correcting"
the numbers back to a 50% threshold.

## Related References

- `.codex/implementation/relic-inventory.md` – summarizes how the Rusty Buckle
  behaves in the player-facing relic catalog and captures the same 50× / 5000%
  trigger math.
- `backend/plugins/relics/rusty_buckle.py` – hosts the implementation and
  inline commentary describing the intentionally inflated threshold used by the
  Aftertaste volley.
