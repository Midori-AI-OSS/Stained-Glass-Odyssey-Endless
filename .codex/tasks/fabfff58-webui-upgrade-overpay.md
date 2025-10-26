# Add optional higher-tier overpay flow to character upgrades

## Problem
Players who enter the roster upgrade view in the WebUI can only confirm an upgrade when they hold the exact star tier required for the next rank. If they are short on 1★ element shards but have a surplus of higher-tier shards (2★/3★/4★), the UI reports that they lack materials and cancels the request. The backend already supports converting higher-tier shards into lower-tier units on demand via `_consume_material_units`, but the Svelte components never expose a way to opt into that conversion. This blocks progression for returning players who stockpiled only higher-tier drops.

## Why this matters
* Party editing in `frontend/src/lib/components/PartyPicker.svelte` and `PlayerPreview.svelte` is a critical onboarding loop; the inability to spend higher-tier shards leads to support tickets and abandoned runs.
* Backend logic in `backend/routes/players.py` allows overspending by converting higher-tier shards into 1★ units, so failing to surface that behavior wastes existing implementation work and confuses players.
* QA has requested UI parity with the mobile build, where the upgrade dialog advertises an "overpay" option when base-tier shards are missing.

## Requirements
* Detect when the active upgrade (`upgradeCosts[stat]`) requires more of the base element shard (e.g., `water_1`) than currently available in the element inventory, but when the summed units across higher tiers (`PlayerPreview.svelte` → `availableMaterials`) is still sufficient to cover the cost.
* Surface a clear prompt inside the upgrade overlay (likely near the status footer rendered in `PlayerPreview.svelte`) that:
  * Explains the shortage of base-tier shards and the availability of higher-tier shards that can be converted.
  * Presents a one-click action to proceed anyway using higher-tier shards. This can be an inline "Overpay with higher-tier shards" button or a confirmation dialog.
  * Shows the exact combination that will be consumed (e.g., "Spend 1× Water 2★ (converts to 125× Water 1★)"), using the existing `formatCost`/`formatMaterialQuantity` helpers from `frontend/src/lib/utils/upgradeFormatting.js`.
* When the player accepts the overpay option, dispatch the same `request-upgrade` event used today but ensure the payload explicitly signals an overpay request. At minimum:
  * Strip the per-tier `breakdown` from `expectedMaterials` before dispatching so the backend can freely convert higher tiers. Keep the `units` field so validation still passes.
  * Include a distinct flag in the payload (e.g., `allowOverpay: true`) so `PartyPicker.svelte` can track the intent and avoid re-prompting the user if the backend responds with partial upgrades.
  * Make sure the `total_materials` budget passed from `PlayerPreview.svelte` uses the full converted unit count so the backend can drain higher tiers as needed.
* Update the error-handling branch in `PartyPicker.svelte` so that an `insufficient materials` response that still reports `materials_available_units >= required_units` automatically re-opens the overpay prompt instead of failing silently.
* Add unit coverage for the new UI state:
  * Extend the Vitest component tests under `frontend/tests/` (add a new test file if needed) to verify that the overpay CTA appears when the inventory only has higher-tier shards and that confirming it dispatches the correct payload to the mock API.
  * Add a regression test around `frontend/src/lib/components/upgradeCacheUtils.js` (or a nearby integration test) to ensure the cache updates correctly when the backend spends higher-tier shards and returns new base-tier counts.
* Document the new flow in `frontend/.codex/implementation/party-ui.md`, describing how the overpay prompt determines eligibility and how it interacts with the backend conversion logic.

## Definition of done
* Players can start an upgrade with zero 1★ shards but sufficient higher-tier shards, see an explanatory prompt, and confirm an overpay that successfully upgrades the stat.
* The upgrade confirmation payload is logged in dev tools showing `allowOverpay` (or similar) and omits a restrictive breakdown, letting `_consume_material_units` handle the conversion.
* Automated tests covering the prompt visibility and payload dispatch pass, and documentation for the party UI upgrade flow is updated.

ready for review
