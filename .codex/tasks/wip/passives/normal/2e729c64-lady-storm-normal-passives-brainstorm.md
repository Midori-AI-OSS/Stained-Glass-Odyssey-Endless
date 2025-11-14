# Task: Brainstorm Normal Tier Tagged Passives for LadyStorm

## Background
LadyStorm's core moveset and lore live in `backend/plugins/characters/lady_storm.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/lady_storm.py`.

## Brainstorm Focus
- Lean into the character's existing kit loops, weapons, and stat hooks.
- Keep mechanics reliable and readable so they can anchor the rest of the tier variants.
- Spot opportunities for QoL or utility twists that feel unique to the character without power creeping boss/prime ideas.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Each option should mention what gameplay loop it reinforces for standard encounters.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/lady_storm.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria [...]

##All Tiers: **Normal: Supercell (IMPLEMENTED)** - Weather control, pressure systems, tornado/hurricane generation | **Prime: Cataclysmic Tempest** - Multi-storm control, weather manipulation absolute | **Boss: Atmospheric Collapse** - **P:** Breeze→Gale→Hurricane→Planetary storm | **Glitched: Weather Malfunction** - Storms target wrong areas, weather inverts, atmospheric readings corrupted
