# Task: Brainstorm Glitched Tier Tagged Passives for Mimic

## Background
Mimic's core moveset and lore live in `backend/plugins/characters/mimic.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/mimic.py`.

## Brainstorm Focus
- Introduce volatility, trade-offs, or corrupted resource loops that still stay fair to fight.
- Show how the glitch motif distorts existing abilities (timing errors, duplicate actions, stat flicker, etc.).
- Account for readability so players can learn to counter or exploit the glitch state.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Capture the glitch fantasy plus the risk/reward profile for each concept.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/mimic.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched: Copy Error (Recommended)
- Targets wrong units (copies allies, self, inanimate objects, air), Abilities corrupted (wrong effects, inverted results, fused randomly), Can't stop copying (stuck in permanent mimic loop), Identity fragmentation (multiple conflicting stat sets active), Visual glitches (model distortion, flickering, wrong textures), Copies future states (mimics actions before they happen) or past states (outdated abilities)

## Glitched: Existential Recursion
- Copies create copies (infinite recursion until stack overflow), Mimic loses original identity (can't revert to base form), Stats accumulate incorrectly (additions become multiplications), Memory leaks (each copy consumes more resources, eventual crash)

**Recommendations:** Copy Error for manageable chaos with comedic potential.
