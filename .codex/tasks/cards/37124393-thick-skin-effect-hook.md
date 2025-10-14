# Fix Thick Skin's bleed duration reduction hook

## Summary
Thick Skin still listens to the legacy `effect_applied(target, effect_name, duration, source)` signature and inspects a non-existent `effect_manager.modifiers` list, so its bleed-shortening effect never triggers under the current EffectManager API.

## Details
* `EffectManager.add_modifier` now emits `effect_applied(effect_name, entity, details)` and stores stat modifiers in `mods`, not `modifiers`.【F:backend/autofighter/effects.py†L397-L433】
* The card's handler expects the old argument order and loops over `effect_manager.modifiers`, which no longer exists, so the body exits without touching DoTs.【F:backend/plugins/cards/thick_skin.py†L17-L39】
* As a result, bleed applications never see their duration reduced, and the `card_effect` event never fires.

## Requirements
- Update the subscription to match the current `effect_applied` payload, including checking `details` to confirm a bleed DoT.
- Inspect the correct EffectManager collections (e.g., `dots`) to locate active bleed effects and safely adjust their `turns` counters.
- Emit the card effect event after a successful reduction and add automated coverage demonstrating that at least one bleed stack loses a turn when the 50% roll succeeds.
