# Battle Room

Describes the backend battle endpoint.

- Exchanges event-bus-driven attacks, comparing player attack against foe defense.
- Foe stats scale with floor, room, Pressure level, and loop count.
- Returns damage numbers, attack effects, and status icons for the frontend to render.
- Each turn increments a counter; after 100 turns (500 for floor bosses) an overtime warning triggers. Foes gain a 40% `Enraged` attack buff every subsequent turn, stacking endlessly, and the battle background cycles between blue and red roughly every ten seconds while enrage is active. The animation slows further when the **Reduced Motion** option is enabled.
- Exiting returns control to the previous room.
- The top navigation bar remains visible during battles, with the home button replaced by a non-interactive battle icon.
- Players can access their inventory during combat via the package icon in the top navigation, allowing them to review collected cards and relics while fighting.
- The reward overlay centers on the battle viewport and sizes to a 1×3 card grid, expanding to 2×3 when six cards are offered.
  Staged entries must include a `preview` payload (summary, stat deltas, and trigger hooks) so `RewardOverlay` can surface
  upcoming buffs before confirmation. Use the backend helpers in `autofighter.reward_preview` when wiring new card or relic
  plugins so preview data stays consistent across reconnects.【F:backend/autofighter/reward_preview.py†L55-L189】【F:frontend/src/lib/utils/rewardStagingPayload.js†L1-L61】
- After a battle, the overlay now includes a right-side stats column that lists each party member and their damage dealt.
- Combat UI places the party in a resizable left column with stats beside each portrait and HoT/DoT markers below; foes mirror the layout on the right. Stats include HP, Attack, Defense, Mitigation, and Crit rate, and shared fallback art is used when portraits are missing. Duplicate HoT/DoT effects collapse into single icons that display stack counts in the bottom-right.
- The frontend polls `roomAction(runId, 'battle', 'snapshot')` once per frame-rate tick to fetch full party and foe snapshots without overloading the CPU and only updates arrays when data differs to reduce re-renders.
- Backend storage helpers like `load_party`, `load_map`, `save_party`, and `save_map` run via `asyncio.to_thread` so battle polling stays responsive and the event loop remains unblocked.
- After battle, a planned "battle review" screen will summarize damage and healing totals for each combatant before allowing the player to advance.
