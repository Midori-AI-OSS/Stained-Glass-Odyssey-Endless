# Task: Brainstorm Boss Tier Tagged Passives for LadyStorm

## Background
LadyStorm's core moveset and lore live in `backend/plugins/characters/lady_storm.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/lady_storm.py`.

## Brainstorm Focus
- Dial up threat pacing via enrages, arena control, multi-phase cues, or punishing counterplay.
- Respect the character fantasy—make the boss feel like an ultimate expression of their personality.
- Consider survivability, anti-burst safeguards, and memorable telegraphs the UI/logs can surface.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Highlight how each idea creates a set-piece moment or new failure condition for parties.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/lady_storm.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria [...]

##Boss/Glitched: **Boss: Atmospheric Collapse** - **P1:** Breeze. **P2(66%):** Gale. **P3(33%):** Hurricane. **P4(<15%):** Planetary storm | **Glitched: Weather Malfunction** - Storms target allies, weather inverts (rain burns), pressure impossible values
