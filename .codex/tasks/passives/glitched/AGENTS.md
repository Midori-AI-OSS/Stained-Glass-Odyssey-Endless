# Task Priority Guidance

Tasks in this folder are lower priority than tasks in the parent `.codex/tasks` directory.

## Glitched Tag Context

Glitched-tier passives are encounter modifiers applied when the foe factory tags a spawned foe as glitched (e.g., `foe.rank = "glitched"` or combined variants like `"glitched boss"`). Glitched passives are not a separate roster—they modify any foe template that receives the glitched tag during spawn via `backend/autofighter/rooms/foe_factory.py::build_encounter`. The modules in `backend/plugins/passives/glitched/` must therefore work safely for every foe that might receive the tag.

Tasks in this folder focus on implementing, balancing, and maintaining glitched-tier passive plugins. Glitched passives should provide warped or enhanced versions of the base character's mechanics that fit the "glitch" theme while remaining compatible with all foe templates. Each glitched passive should maintain the character's voice, mechanical motifs, and resource systems rather than applying generic buffs.

Documentation reminder: glitched passive plugins capture the official behaviour and descriptive copy in their `about`/`describe()` output. Do not request updates to `.codex/implementation/relic-system.md` or parallel summary docs when writing or reviewing glitched passive tasks; keeping the plugin modules accurate is sufficient.
