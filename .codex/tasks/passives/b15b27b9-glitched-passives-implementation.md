# Task: Implement Glitched-Tier Passive Plugins

## Background
Glitched characters are supposed to lean on distorted versions of our normal passives, but the modules under
`backend/plugins/passives/glitched/` are just empty stubs. Each file only contains a comment and `pass`, so the plugin loader
registers nothing for glitched variants (see `backend/plugins/passives/glitched/kboshi_flux_cycle.py` lines 1-3 for a typical
example). Without concrete classes, any character that tries to load a `glitched` passive will receive a missing plug-in error.

## Problem
We cannot assign glitched-tier passives because there are no classes to instantiate. The placeholders also make it unclear
whether we should fall back to the normal versions or implement bespoke behaviour. This leaves the glitched roster unusable
and blocks future balance work.

## Requested Changes
- Decide on an approach for glitched passives: either subclass/wrap the normal implementations with glitched-specific tweaks or
  provide distinct behaviour that fits the glitch theme. Document the decision inside the module docstrings.
- Replace every `pass` file in `backend/plugins/passives/glitched/` with a concrete plug-in class that sets `plugin_type = "passive"`,
  exposes the expected metadata (`id`, `name`, `trigger`, `max_stacks`, etc.), and implements the appropriate async hooks.
- Ensure each plug-in registers cleanly with the `PluginLoader` (import side effects are enough, but include a simple unit test or
  loader smoke test in `backend/tests/` to prevent regressions).
- Capture the glitched behaviour in each plugin's `about`/`describe()` output so roster references pull directly from code.

## Acceptance Criteria
- All files in `backend/plugins/passives/glitched/` define real plug-in classes (no raw `pass` placeholders remain).
- Loading the passive registry (e.g., via `PassiveRegistry()._registry`) exposes the glitched IDs without errors.
- Automated coverage confirms at least one glitched passive executes its custom logic.
- Plugin metadata reflects the availability and intent of the glitched-tier passives.
