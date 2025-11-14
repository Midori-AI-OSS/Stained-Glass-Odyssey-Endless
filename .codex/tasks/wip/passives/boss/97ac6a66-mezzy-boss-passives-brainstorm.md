# Task: Brainstorm Boss Tier Tagged Passives for Mezzy

## Background
Mezzy's core moveset and lore live in `backend/plugins/characters/mezzy.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/mezzy.py`.

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
- Character plugin: `backend/plugins/characters/mezzy.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Boss: The Devourer (Recommended)
**Phase 1 (100-66%):** Enhanced absorption (3× rate), passive stat siphon each turn from all enemies
**Phase 2 (66-33%):** Mass Siphon - automatic drain aura, all enemies lose stats constantly, Mezzy grows visibly larger
**Phase 3 (33-0%):** True Hunger - starts consuming terrain/environment (creates hazard zones), size massive, "Consumption Field" pulls enemies toward center  
**Finale:** At death, attempts to devour entire arena (party must escape or finish quickly)

## Boss: Endless Feast
- Never stops growing (stat cap removed), Each enemy death feeds Mezzy (absorbs all stats), At 500 total stats: "Singularity Form" (becomes black hole, constant pull + crush damage), Must be defeated before full transformation

**Recommendations:** The Devourer for environmental storytelling.
