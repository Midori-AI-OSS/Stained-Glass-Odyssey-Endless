# Task Priority Guidance

Tasks in this folder are lower priority than tasks in the parent `.codex/tasks` directory.

## Prime Tag Context

Prime-tier passives are encounter modifiers applied when the foe factory tags a spawned foe as prime (e.g., `foe.rank = "prime"` or combined variants like `"prime boss"`). Prime passives are not a separate roster—they annotate any foe template that receives the prime tag when `backend/autofighter/rooms/foe_factory.py::build_encounter` rolls the prime probability. The modules in `backend/plugins/passives/prime/` must therefore be safe wrappers or upgrades that can layer on top of the base character without requiring additional spawn setup.

Tasks in this folder focus on implementing, balancing, and maintaining prime-tier passive plugins. Prime passives should deliver power spikes and mechanical twists that justify the prime tier, with upgrades like stronger effects, additional triggers, or enhanced capabilities. Each prime variant should read like an exalted version of that specific character rather than a generic power increase, maintaining the character's theme and identity.

Documentation reminder: prime passive plugins capture the official behaviour and descriptive copy in their `about`/`describe()` output. Do not request updates to `.codex/implementation/relic-system.md` or parallel summary docs when writing or reviewing prime passive tasks; keeping the plugin modules accurate is sufficient.
