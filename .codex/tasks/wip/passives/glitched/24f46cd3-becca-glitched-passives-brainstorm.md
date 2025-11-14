# Task: Brainstorm Glitched Tier Tagged Passives for Becca

## Background
Becca's core moveset and lore live in `backend/plugins/characters/becca.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/becca.py`.

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
- Character plugin: `backend/plugins/characters/becca.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched: Pet Instability (Recommended)
- Pets spawn/despawn randomly each turn (50% chance either way), Wrong pet types summon (cats, dogs, dragons instead of jellyfish), Pets target randomly (40% correct enemy, 30% wrong enemy, 30% ally), Bond values display corrupted and fluctuate wildly (-50% to +200%), Pets can merge unexpectedly into chimera abominations

## Glitched: Quantum Pets
- Pets exist in superposition (visible but intangible 50% of time), Pet actions occur in random order (before or after Becca's turn), Pet count displays as "NULL" or negative numbers, Pets can phase through walls/boundaries, Bond triggers on non-pet-related events

**Recommendations:** Pet Instability for manageable chaos with visual comedy.
