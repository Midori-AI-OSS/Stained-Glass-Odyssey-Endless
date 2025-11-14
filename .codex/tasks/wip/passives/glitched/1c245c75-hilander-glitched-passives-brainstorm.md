# Task: Brainstorm Glitched Tier Tagged Passives for Hilander

## Background
Hilander's core moveset and lore live in `backend/plugins/characters/hilander.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/hilander.py`.

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
- Character plugin: `backend/plugins/characters/hilander.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched Concepts

### Option 1: Quantum Fermentation (Recommended)
- Stack count displays as corrupted: "?##?" or random values
- Actual stacks exist in superposition until "observed" (on crit)
- Crit damage based on random stack count between 0-50 (not actual stacks)
- 25% chance crit doesn't consume stacks (stays in quantum state)
- Random crits occur unpredictably (5-15% chance/hit regardless of stats)

**Glitch-Worthy:** Deterministic system becomes probabilistic chaos.

### Option 2: Inverted Fermentation
- Stacks build in reverse: Start at 20, lose 1 per hit
- At 0 stacks: Auto-crit and reset to 20
- Crit damage inversely proportional to stacks (fewer stacks = bigger crit)
- Random +5-10 stack jumps disrupt countdown
- Can go negative (glitch state): Negative stacks heal enemies on crit

**Glitch-Worthy:** Inverted logic, countdown vs buildup.

### Option 3: Unstable Release
- Normal stacking, but crit timing becomes unreliable
- 40% chance crit releases normally
- 30% chance partial release (50% stacks consumed, 50% damage)
- 20% chance over-release (150% stacks worth of damage, lose extra stacks)
- 10% chance misfire (consume stacks, no crit)

**Glitch-Worthy:** Release mechanism corrupted, output unpredictable.

**Recommendations:** Quantum Fermentation for pure chaos, Inverted for learnable pattern.
