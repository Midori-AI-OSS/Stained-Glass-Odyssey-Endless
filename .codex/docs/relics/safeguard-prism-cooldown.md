# Safeguard Prism Cooldown Rationale

Safeguard Prism now re-arms on a fixed turn timer instead of burning one trigger
per stack. Each activation grants 15% Max HP shields and +12% mitigation per
stack, but the ally must wait **5 turns plus 1 additional turn for every full 5
stacks** before the relic can fire again. This keeps the relic reliable during
extended battles without letting high-stack parties loop permanent shields.

Cooldown timers track the number of BUS `turn_start` events that have elapsed.
Turn counts reset on `battle_start` and any ready ally clears their cooldown
entry once the stored turn threshold has passed. Telemetry now reports the
current turn, the next available turn, and the number of turns remaining so
logs show exactly when the relic will re-trigger.

