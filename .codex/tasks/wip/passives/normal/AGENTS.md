# Normal Tier Passive Tasks - Work In Progress

Normal-tier passives represent the baseline implementations for character passive abilities. These are found in `backend/plugins/passives/normal/` and serve as the foundation for all passive behaviour. Normal passives should be clean, standalone implementations without hard-coded branches for boss, glitched, or prime modifiers—those tier-specific behaviours belong in their respective folders.

Tasks in this folder focus on implementing, balancing, and maintaining normal-tier passive plugins. As tiered passive variants (boss, glitched, prime) are implemented, normal passives should have their hard-coded tier-specific logic removed and replaced with clean baseline behaviour. This ensures the tier system remains modular and maintainable.

Documentation reminder: normal passive plugins capture the official behaviour and descriptive copy in their about/describe() output. Do not request updates to `.codex/implementation/relic-system.md` or parallel summary docs when writing or reviewing normal passive tasks; keeping the plugin modules accurate is sufficient.
