# Task: Brainstorm Glitched Tier Tagged Passives for Kboshi

## Background
Kboshi's core moveset and lore live in `backend/plugins/characters/kboshi.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/kboshi.py`.

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
- Character plugin: `backend/plugins/characters/kboshi.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched: Element Corruption (Recommended)
- Random "NULL" element (no type, bypasses resistances but deals reduced damage)
- Inverted elements: Fire→freeze, Ice→burn, Light→blind allies, Dark→illuminate
- Impossible elements: "Quantum" (hits past/future state), "Void" (erases buffs), "Chaos" (random effect)
- Element can corrupt mid-attack (start fire, end ice)
- HoT becomes "HoX" (Healing-or-Toxic, 50/50 chance each tick)
- Display shows glitched element names: "F##E", "░░░", "ERROR"

## Glitched: Flux Instability
- Element cycle becomes non-linear (can skip, repeat, reverse)
- Stack gains randomized (-5 to +15/turn)
- Element locks randomly (stuck on one for 1-5 turns)
- Sudden element purges (all stacks vanish, instant re-roll)

**Recommendations:** Element Corruption for thematic glitch chaos.
