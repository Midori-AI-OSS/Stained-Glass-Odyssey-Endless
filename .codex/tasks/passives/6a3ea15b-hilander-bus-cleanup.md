# Hilander Critical Ferment bus cleanup

## Summary
Hilander's `Critical Ferment` passive subscribes to the global `critical_hit`
event but never unregisters when Hilander is defeated while stacks remain. The
callback persists for the rest of the run, leaking listeners and leaving the
`_hilander_crit_cb` attribute on the defeated unit.

## Details
* The passive registers a callback the first time it applies stacks and only
  unsubscribes if all stacks are consumed or the weakref target disappears. There
  is no defeat/battle-end cleanup. 【F:backend/plugins/passives/normal/hilander_critical_ferment.py†L67-L123】
* The passive registry already invokes `on_defeat` hooks, so we can hook into
  that to remove the subscription and clear the helper attribute.
  【F:backend/autofighter/passives.py†L152-L172】

## Tasks
1. Add a defeat (and/or battle-end) handler to `HilanderCriticalFerment` that
   unsubscribes `_hilander_crit_cb` if present and removes the stored attribute.
2. Ensure the handler is safe to call when no listener has been registered and
   does not raise if called multiple times.
3. Add a regression test that equips the passive, triggers it, then simulates
   defeat to confirm the bus listener and attribute are cleared.

## Definition of Done
* Hilander no longer leaves behind a `critical_hit` subscription after defeat.
* Automated test coverage confirming the cleanup.

ready for review
