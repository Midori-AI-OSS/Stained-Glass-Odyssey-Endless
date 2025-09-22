# Passive System Planning

## Goal
Integrate the existing plugin-based passive system into the web build while expanding support for new effects.

## Actionable Steps
1. **Plugin Migration**
   1. Review current passive plugins in `plugins/passives` and document their behaviors.
   2. Port the plugin loader to the new backend, ensuring lazy discovery and low-end performance.
   3. Define a registration schema so passives declare triggers (on hit, on turn start, etc.) and stack limits.
2. **UI and Player Hooks**
   1. Expose active passives on the player stat screen with names, brief summaries, and stack counts.
   2. Provide in-run previews when selecting new relics or gacha characters that grant passives.
   3. Add hooks in combat loops so passives can modify stats, apply DoTs, or create other side effects.
3. **Testing**
   1. Create unit tests validating plugin discovery, stacking, and trigger resolution.
   2. Add sample passives for smoke testing in battles and map events.

## Open Questions
- Should passives be upgradeable separately from relics, or should relic stacking handle all passive scaling?
- What debugging tools are needed to track passive activations during automated fights?
