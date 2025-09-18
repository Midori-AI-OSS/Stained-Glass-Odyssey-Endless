# Login Reward Panel

`LoginRewardsPanel.svelte` renders the centered banner on the home screen and
drives the daily login reward flow.

## Layout
- Absolute positioned banner that centers above the main menu grid on desktop
  and reflows into a full-width card on narrow screens.
- Chevron badges visualize the current streak. Up to 12 days are displayed; an
  ellipsis prefix appears when streaks exceed the window so the latest days stay
  visible.
- Countdown row lists the local time remaining until the next 2 AM PT reset and
  shows the concrete reset timestamp for tooltips.
- A progress card tracks the "three rooms per day" requirement and surfaces the
  current count as both a numeric label and animated progress bar.
- Reward entries render as grid chips with star icons, item names, and the
  damage type/ID metadata surfaced by the backend.

## Behaviour
- Fetches `/rewards/login` on mount, when the tab regains focus, after manual
  refresh clicks, and after successful claims.
- Keeps a short `MIN_REFRESH_INTERVAL` guard so repeated UI events do not spam
  the backend. Manual refresh still bypasses the guard.
- Stores the `seconds_until_reset` countdown locally, decrementing once per
  second. When the counter hits zero the panel schedules a forced refresh to
  pick up the next day's bundle.
- Claim button disables itself until `can_claim` is true and switches to a
  confirmation state when `claimed_today` is returned by the backend.
- Errors from either fetch or claim requests are surfaced inline to avoid
  triggering a full-screen overlay when the panel fails in isolation.
