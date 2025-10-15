# Oracle Prayer Charm: Ryne-flavored 1★ rescue drip

## Summary
The 1★ catalog leans on flat stat bumps or tiny reactive procs, but none of the low-rank cards provide a Light-style safety net once Sturdy Vest's small HoT runs out.【F:.codex/implementation/card-inventory.md†L12-L47】 Ryne's kit revolves around layering Oracle-of-Light wards and mid-fight stabilizers, so a charm that sprinkles Radiant Regeneration when allies are in danger fits both her theme and the roster fiction.【F:.codex/implementation/player-foe-reference.md†L51-L70】【F:.codex/implementation/damage-healing.md†L12-L36】

## Details
* Implement **Oracle Prayer Charm** as a 1★ card that grants +3% Effect Resistance and +3% Vitality to emphasize Ryne's protective aura while nudging survivability-focused builds.【F:.codex/implementation/card-inventory.md†L12-L47】【F:.codex/implementation/player-foe-reference.md†L51-L70】
* Subscribe to the battle event bus so that the first time each party member begins a turn below ~45% HP in a battle, they receive a 2-turn `Radiant Regeneration` HoT. Track per-member triggers to avoid infinite refreshes and reuse the existing HoT plugin instead of inventing a bespoke heal.【F:.codex/implementation/damage-healing.md†L12-L36】【F:.codex/implementation/stats-and-effects.md†L33-L63】
* Emit rich telemetry on each trigger (who received the HoT, HP threshold, remaining charges) so battle logs surface when the charm saves someone.

## Requirements
- Add `backend/plugins/cards/oracle_prayer_charm.py` with the stats + trigger logic above, mirroring subscription cleanup patterns used by other 1★ reactive cards like Balanced Diet and Sturdy Vest.
- Extend backend card tests to cover edge cases: multiple allies dipping under the threshold, ensuring once-per-ally limits reset after `battle_end`, and verifying Radiant Regeneration is applied using the shared HoT class.
- Update `.codex/implementation/card-inventory.md` and `.codex/planning/archive/726d03ae-card-plan.md` with the new entry and tuning notes.【F:.codex/implementation/card-inventory.md†L12-L69】【F:.codex/planning/archive/726d03ae-card-plan.md†L5-L69】
- Supply a placeholder icon (`oracleprayercharm.png`) under `frontend/src/lib/assets/cards/Art/` and confirm the asset registry picks it up with the usual glob scan.【F:frontend/src/lib/systems/assetRegistry.js†L245-L253】

---

ready for review
