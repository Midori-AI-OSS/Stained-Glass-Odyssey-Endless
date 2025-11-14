# Task: Brainstorm Glitched Tier Tagged Passives for Ryne

## Background
Ryne's core moveset and lore live in `backend/plugins/characters/ryne.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/ryne.py`.

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
- Character plugin: `backend/plugins/characters/ryne.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched: Chaotic Scales (Recommended)
- Balance calculations use wrong stats (MP instead of HP, ATK vs DEF, random), Equilibrium effects inverted (penalties when balanced, bonuses when imbalanced), HP redistribution targets wrong units (can kill allies accidentally), Display shows impossible values ("150%/−50%", "NaN", "∞"), "Negative balance" possible (HP goes below 0 but units don't die), Time dilation triggers randomly regardless of balance state

## Glitched: Quantum Superposition
- All units exist at multiple HP values simultaneously (schrodinger's health bar), Balance state flickers between extremes each turn, Healing and damage apply to random HP state, "Observation" collapses waveform (locks to one HP value for 1 turn)

**Recommendations:** Chaotic Scales for unpredictable but learn-able patterns.
