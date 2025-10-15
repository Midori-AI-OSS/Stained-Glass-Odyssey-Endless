# Battle Rooms

`BattleRoom` resolves turn-based encounters against scaled foes drawn from player plugins you haven't selected. Passives fire on room entry, battle start, and at the beginning and end of each turn. Combat continues until either every party member or the foe is defeated. All damage, healing, and regeneration helpers are awaitable, and each turn is padded to last at least `TURN_PACING` (0.5 s) before waiting another `TURN_PACING` to keep updates visible. The pacing default is shared with the `/config/turn_pacing` API and Settings UI slider so refreshing configuration no longer snaps players to different values. The `EffectManager` applies damage-over-time and healing-over-time ticks on each combatant before actions take place, and the async loop yields with `await asyncio.sleep(0.001)` between steps so DoTs and HoTs remain non-blocking.

The room deep-copies the run's party for combat. When the fight ends, remaining
HP and accumulated experience are synced back so level-ups and damage persist
into subsequent rooms. `SummonManager.reset_all()` runs at battle start so all
summons and related tracking are cleared, preventing leftovers from leaking
into later encounters.

Snapshot overlays keep a rolling record of the latest combat events so the
frontend can poll without missing bursts of activity. The backend now retains
the forty most recent entries per run—enough to preserve multiple turns of
effect ticks, relic triggers, and combat results—while still capping payloads
so websocket updates stay lightweight.

## Action Queue Flow

Turn order is governed by an Action Gauge system. Each combatant starts the
battle with an ``action_gauge`` of ``10,000``.  A combatant's base
``action_value`` is calculated as ``10,000 / SPD``.

1. Build a queue sorted by each combatant's current ``action_value``.
2. The fighter with the lowest value acts first.
3. After the actor's turn completes, subtract the amount spent from every other
   combatant's ``action_value``.
4. Reset the actor's ``action_value`` to its stored base value and reinsert it
   at the end of the queue.

This loop repeats until either the party or all foes fall. The queue state is
exposed for the frontend to visualize upcoming turns.

The battle UI displays the queue as a horizontal strip of combatant portraits.
The active fighter is outlined, and when its turn ends the portrait slides to
the back of the line. Enabling the **Show Action Values** setting reveals each
fighter's current ``action_value`` beneath their portrait for debugging turn
order.

### Queue Manipulation

Some skills grant an immediate extra turn.  When this happens the backend marks
the triggering combatant for a bonus action and the snapshot inserts an extra
portrait at the front of the queue.  The bonus portrait is dimmed in the UI so
players can anticipate the upcoming repeat action without confusing it for the
currently active fighter.  After the bonus turn resolves, the queue resumes
normal sequencing without advancing other gauges.

[Action Animation Timers task](../tasks/cbd1caee-action-animation-timers.md)
tracks upcoming work on per-action delays and animation hooks.

### Timing and Animation

Each action reports an ``animation_duration`` in seconds. The battle loop waits
for that duration plus ``TURN_PACING`` (0.5 s) before progressing so long
animations do not clip subsequent turns.

For example, a skill with a 1.2 s animation blocks the queue for roughly
1.7 s (``1.2 + TURN_PACING``) before the next combatant acts.

### Intro pacing

Room introductions now derive their delay from the staged cinematic queue rather than a fixed ``3 / TURN_PACING`` sleep. When cinematics are queued, `_intro_pause_seconds` multiplies the number of combatants by ``0.25`` seconds, caps the wait at ``1.75`` seconds, and then delegates to `pace_sleep` so the delay respects turn pacing adjustments. If the queue is empty, the helper returns immediately and the intro banner is skipped, eliminating the 15 s pause players previously encountered at the old backend default.

Developers can preview numeric action values by enabling the debug toggle
documented in [Action Value Display instructions](../instructions/action-value-display.md).
Adjust global pacing in the [options menu](../instructions/options-menu.md).

Each strike rolls the attacker's `effect_hit_rate` against the target's `effect_resistance`. The difference is clamped to zero, jittered by ±10%, and even a failed roll has a 1% floor chance to attach a damage-type-specific DoT scaled to the damage dealt.

During the foe's turn, a target is chosen from living party members with a probability weight of `defense × mitigation`, making sturdier allies more likely to draw aggro.

`BossRoom` subclasses `BattleRoom` but multiplies foe stats by 100× to create floor bosses.
Boss encounters always spawn exactly one foe regardless of party size or pressure.

Experience is awarded as soon as a foe falls, allowing multiple enemies to grant cumulative rewards. When the fight ends, the backend returns updated party stats, card choices, and foe data so the run map can advance.

# Loop scaling

Foe stats scale via `balance.loop.scale_stats`, multiplying base values by floor, room, and loop counts. Floor bosses apply an extra `100×` base factor. Tuning knobs live in `balance.loop.config` for adjusting loop multipliers without touching combat logic.

# Battle room rewards

Rewards draw from a Rare Drop Rate (RDR) that starts at zero and rises with floor, room index, and any bonuses from relics or cards. Higher RDR increases the odds of rarer stars while proportionally reducing common ones. Card rewards roll star ranks using these baseline odds; regular battles only offer 1★ or 2★ cards, bosses extend the table up to 5★, and floor bosses guarantee 3★ or better. Percentages below reflect baseline odds at RDR 0.
Each foe killed during combat adds a temporary 55% RDR boost for that room,
further increasing gold and element upgrade item drops.

Normal fights:
- 5% chance to drop a relic (1★ at 98%, 2★ at 2%).
- Upgrade items: 80% 1★, 20% 2★.
- Cards: 80% 1★, 20% 2★.
- Gold: `5 × loop × rand(1.01, 1.25)`.

Boss fights:
- 25% chance to drop a relic (1★ 40%, 2★ 30%, 3★ 0.15%, 4★ 0.10%, 5★ 0.05%).
- Upgrade items: 60% 1★, 39.9% 2★, 0.10% 3★.
- Cards: 40% 1★, 30% 2★, 0.15% 3★, 0.10% 4★, 0.05% 5★.
- Gold: `20 × loop × rand(1.53, 2.25)`.

Floor bosses:
- Guaranteed relic drop (3★ at 0.98%, 4★ at 0.02%, 5★ at 0.0002%).
- Upgrade items: 0.8% 3★, 0.2% 4★.
- Cards: 0.6% 3★, 0.25% 4★, 0.15% 5★.
