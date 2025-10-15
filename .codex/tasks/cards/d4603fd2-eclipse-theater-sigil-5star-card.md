# Eclipse Theater Sigil: Persona Light/Dark 5★ rotation

## Summary
Our 5★ options currently cover summon tempo, near-invulnerability, and crit-stacked echoes, but none capture Persona Light and Dark's alternating aura that flips between radiant support and oppressive debuffs.【F:.codex/planning/archive/726d03ae-card-plan.md†L66-L69】【F:.codex/implementation/player-foe-reference.md†L68-L70】 Delivering a toggle that swaps Light heals and Dark pressure each turn would broaden endgame builds beyond raw damage spikes.

## Details
* Introduce **Eclipse Theater Sigil** as a 5★ card granting +1500% Max HP and +1500% ATK so it meaningfully boosts both sides of the dual persona fantasy.【F:.codex/planning/archive/726d03ae-card-plan.md†L66-L69】【F:.codex/implementation/player-foe-reference.md†L68-L70】
* Maintain a global polarity flag: Light turns (odd overall turns) should cleanse one DoT from each ally and apply a 2-turn `Radiant Regeneration`; Dark turns (even turns) should apply one stack of `Abyssal Weakness` to all foes and give every ally a 1-action +50% crit rate buff to represent the aggressive surge. Reset ally-specific crit buffs after they consume the bonus to avoid stacking indefinitely.【F:.codex/implementation/damage-healing.md†L7-L23】【F:.codex/implementation/stats-and-effects.md†L33-L73】
* Emit telemetry describing the chosen polarity, dispelled debuffs, applied DoTs, and crit buffs so replay logs can confirm the alternating cadence.

## Requirements
- Implement `backend/plugins/cards/eclipse_theater_sigil.py` with stat mods, turn-based polarity toggles, ally/foe effect application, crit buff cleanup, and subscription teardown patterned after Reality Split and Temporal Shield.
- Extend backend tests to cover alternating turns, ensuring cleanses happen only on Light turns, Dark debuffs/buffs fire once per turn, and polarity resets between battles.
- Document the new card in `.codex/implementation/card-inventory.md` (adding the missing 5★ section if needed) and refresh the archived card plan with the alternating aura description.【F:.codex/implementation/card-inventory.md†L63-L69】【F:.codex/planning/archive/726d03ae-card-plan.md†L66-L69】
- Drop `eclipsetheatersigil.png` into `frontend/src/lib/assets/cards/Art/` and confirm the UI catalogs it.
