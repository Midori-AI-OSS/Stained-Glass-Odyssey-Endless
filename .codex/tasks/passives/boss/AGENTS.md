# Task Priority Guidance

Tasks in this folder are lower priority than tasks in the parent `.codex/tasks` directory.

## Boss Tag Context

Boss-tier passives are encounter modifiers applied when the foe factory tags a spawned foe as a boss (e.g., `foe.rank = "boss"` or combined variants like `"glitched boss"` or `"prime boss"`). Boss passives are not a separate roster—they enhance any foe template that receives the boss tag during spawn. The modules in `backend/plugins/passives/boss/` must therefore be safe wrappers or upgrades that layer on top of the base character's stats and abilities.

Tasks in this folder focus on implementing, balancing, and maintaining boss-tier passive plugins. Boss passives should provide tier-appropriate enhancements that justify the increased difficulty, while maintaining each character's narrative and mechanical theme. Boss variants should feel like climactic expressions of their base characters rather than generic stat increases.

Documentation reminder: boss passive plugins capture the official behaviour and descriptive copy in their `about`/`describe()` output. Do not request updates to `.codex/implementation/relic-system.md` or parallel summary docs when writing or reviewing boss passive tasks; keeping the plugin modules accurate is sufficient.
