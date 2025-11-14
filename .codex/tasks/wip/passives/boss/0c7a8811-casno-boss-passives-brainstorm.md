# Task: Brainstorm Boss Tier Tagged Passives for Casno

## Background
Casno's core moveset and lore live in `backend/plugins/characters/casno.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/casno.py`.

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
- Character plugin: `backend/plugins/characters/casno.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Boss: Eternal Flame (Recommended)
**Phase 1 (100-60%):** Normal respite + passive momentum gain
**Phase 2 (60-30%):** Self-Resurrection - First death triggers revival at 50% HP with fire nova
**Phase 3 (30-0%):** Immolation - Permanent fire aura (constant party healing + enemy burn), momentum locked at max
**Death Trigger:** Phoenix Rebirth - Resurrects all defeated allies at 25% HP, then final death

## Boss: Flame Cycle
- Dies and resurrects automatically every 25% HP loss
- Each resurrection: Stronger (+ 25% all stats), faster momentum, larger aura
- Must kill 4 times total (100→75→50→25→0)
- Final phase: Desperate Inferno (screen-wide fire damage)

**Recommendations:** Eternal Flame for epic multi-phase phoenix fantasy.
