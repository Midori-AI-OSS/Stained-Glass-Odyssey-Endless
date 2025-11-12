# Task Priority Guidance

Tasks in this folder are lower priority than tasks in the parent `.codex/tasks` directory.

## Folder Organization

This folder contains tag-specific subfolders for organizing passive implementation tasks:

- **boss/** - Tasks related to boss-tier passive modifiers
- **glitched/** - Tasks related to glitched-tier passive modifiers
- **prime/** - Tasks related to prime-tier passive modifiers
- **normal/** - Tasks related to normal-tier (baseline) passive implementations

Each subfolder has its own AGENTS.md file explaining the context and purpose of that specific tag tier. Passive modifiers (boss, glitched, prime) are encounter-based tags applied by the foe factory and layer on top of base character implementations.

Documentation reminder: passive plugins capture the official behaviour and descriptive copy. Do not request updates to `.codex/implementation/relic-system.md` or parallel summary docs when writing or reviewing passive tasks; keeping the plugin accurate is enough.
