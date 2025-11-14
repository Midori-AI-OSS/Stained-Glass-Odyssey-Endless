# Task: Brainstorm Glitched Tier Tagged Passives for Casno

## Background
Casno's core moveset and lore live in `backend/plugins/characters/casno.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/casno.py`.

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
- Character plugin: `backend/plugins/characters/casno.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched: Unstable Combustion (Recommended)
- Healing randomized each tick: 0%-300% of normal (average 150%)
- Momentum system corrupted:
  - Can go negative (below 0 = anti-healing damage pulses)
  - Builds on attacking instead of relaxing (inverted)
  - Random momentum jumps ±10 per turn
- Flames flicker: 50% chance flames extinguish completely each turn (must rebuild)
- Resurrection glitch: 25% chance to resurrect as enemy (friendly fire mode for 2 turns)
- Display shows corrupted momentum: "RELAX: ░#█" or negative values

## Glitched: Phoenix Paradox
- Death and resurrection happen simultaneously (quantum state)
- Exists as alive AND dead (50% damage taken, 50% healing received)
- Flames both heal and burn (damages self while healing allies)
- Respite pulse timing becomes non-linear (can trigger before/after turn randomly)

**Recommendations:** Unstable Combustion for manageable chaos with risk/reward.
