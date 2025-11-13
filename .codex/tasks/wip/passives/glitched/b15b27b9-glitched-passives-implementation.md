# Task: Implement Glitched-Tier Passive Plugins

## Background
Glitched tags are encounter modifiers that get layered onto any foe template when the spawn roll marks it as glitched.
`backend/autofighter/rooms/foe_factory.py::build_encounter` simply toggles `foe.rank = "glitched"` (or `"glitched boss"`)
and does not spawn a bespoke roster. Because of that design, the modules under `backend/plugins/passives/glitched/` must work
for *every* foe that might receive the tag. Today those modules are empty stubs. Each file only contains a comment and `pass`,
so the plugin loader registers nothing for glitched variants (see `backend/plugins/passives/glitched/kboshi_flux_cycle.py`
lines 1-3 for a typical example). The stop-gap has been to cram glitched behaviour into the default passive—see
`backend/plugins/passives/normal/luna_lunar_reservoir.py` where `_is_glitched_nonboss()` branches double Luna's charge and sword
effects. That hard-coding breaks the “attach modifiers as separate passives” plan and makes it impossible to give other foes
matching treatment. Without concrete classes, any character that rolls the `glitched` modifier ends up with missing plug-in
errors during spawn and forces bespoke hacks in their base passives.

## Problem
We cannot assign glitched-tier passives because there are no classes to instantiate. The placeholders also make it unclear
whether we should fall back to the normal versions or implement bespoke behaviour that stacks on top of the base foe. Since
every foe can gain a glitched tag via the factory, the absence of real passives leaves glitched encounters unusable and blocks
future balance work. It also keeps us stuck with copy-pasted `if "glitched" in rank` conditionals buried in normal passives, which
is exactly what we are trying to remove for characters like Luna Midori.

## Requested Changes
- Decide on an approach for glitched passives: either subclass/wrap the normal implementations with glitched-specific tweaks or
  provide distinct behaviour that fits the glitch theme *while remaining safe for any foe template that may roll the tag*.
  Document the decision inside the module docstrings so future changes to `FoeFactory` or spawn percentages keep the same mental model.
- Replace every `pass` file in `backend/plugins/passives/glitched/` with a concrete plug-in class that sets `plugin_type = "passive"`,
  exposes the expected metadata (`id`, `name`, `trigger`, `max_stacks`, etc.), and implements the appropriate async hooks.
- Ensure each plug-in registers cleanly with the `PluginLoader` (import side effects are enough, but include a simple unit test or
  loader smoke test in `backend/tests/` that spawns foes through `FoeFactory` with a forced `glitched` roll to prevent regressions).
- As the new modules come online, remove glitched-specific hacks from the base passive files (e.g., `luna_lunar_reservoir.py`)
  so each character’s default passive is agnostic of encounter modifiers and the glitched variant lives entirely in the matching
  `backend/plugins/passives/glitched/<character>.py`.
- Keep each glitched passive firmly on theme for its character—reuse the same voice, mechanical motifs, and resource systems so the modifier
  feels like a warped version of that character rather than a generic buff with no personality.
- Capture the glitched behaviour in each plugin's `about`/`describe()` output so roster references pull directly from code.

## Acceptance Criteria
- All files in `backend/plugins/passives/glitched/` define real plug-in classes (no raw `pass` placeholders remain) that can attach to any foe instance.
- Loading the passive registry (e.g., via `PassiveRegistry()._registry`) exposes the glitched IDs without errors.
- Automated coverage confirms at least one glitched passive executes its custom logic when a foe spawned via `FoeFactory.build_encounter()` is forced to be glitched.
- Plugin metadata reflects the availability and intent of the glitched-tier passives, including notes that these are encounter modifiers rather than new standalone characters.
- Normal-tier passives (e.g., `backend/plugins/passives/normal/luna_lunar_reservoir.py`) no longer hard-code glitched logic once their dedicated variant exists.
