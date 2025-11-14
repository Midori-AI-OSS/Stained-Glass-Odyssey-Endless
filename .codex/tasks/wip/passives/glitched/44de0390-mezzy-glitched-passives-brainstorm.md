# Task: Brainstorm Glitched Tier Tagged Passives for Mezzy

## Background
Mezzy's core moveset and lore live in `backend/plugins/characters/mezzy.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/mezzy.py`.

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
- Character plugin: `backend/plugins/characters/mezzy.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched: Corrupted Consumption (Recommended)
- Absorption direction inverts randomly (50% chance: loses stats instead of gaining), Siphoned stats distributed randomly (40% to self, 30% to random ally, 30% to random enemy), Can accidentally "eat" allies (drains friendly units), Hunger meter corrupted (displays backwards, negative values, or "OVERFLOW"), Temporary buffs become permanent debuffs unpredictably, Size fluctuates wildly (microscopic to gigantic randomly)

## Glitched: Metabolic Collapse  
- Absorption causes "indigestion" (damage over time), Stats gained are unstable (decay rapidly or spike randomly), "Anti-hunger" state possible (must actively avoid absorbing or take damage), Siphon targeting broken (hits self or wrong units)

**Recommendations:** Corrupted Consumption for chaotic risk/reward gameplay.
