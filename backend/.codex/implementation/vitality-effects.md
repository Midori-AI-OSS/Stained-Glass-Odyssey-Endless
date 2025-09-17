# Vitality effects

- Direct healing and healing over time scale with both the healer's vitality and the target's vitality: `healing * healer_vitality * target_vitality`.
- Damage over time uses the same vitality modifiers as direct damage; source vitality increases damage while target vitality reduces it with a minimum of 1 per tick.
- Healing over time ticks resolve before damage over time, allowing recovery to mitigate upcoming damage each turn.
- Light damage type users grant all allies a stack of Radiant Regeneration
  (5 HP over 2 turns) on each action and will directly heal allies under 25%
  HP instead of attacking.
- Dark damage type users siphon 10% of each living ally's current HP whenever
  they act, never reducing anyone below 1 HP. The health drained contributes to
  a temporary damage multiplier on their next strike (roughly 0.0001× per HP
  siphoned with slight randomness), after which the bonus is cleared.
- Wind damage type users strike all remaining foes after their first hit,
  repeating the damage and rolling their Gale Erosion DoT on each target.
- When a Wind user fires their ultimate, all existing enemy DoTs are pulled
  onto the chosen target and detonate immediately.
- Frozen Wound stacks reduce actions per turn and give the afflicted unit a
  `1% × stacks` chance to miss their next action.
