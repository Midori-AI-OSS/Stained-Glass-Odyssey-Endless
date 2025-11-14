# Task: Brainstorm Prime Tier Tagged Passives for Hilander

## Background
Hilander's core moveset and lore live in `backend/plugins/characters/hilander.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/hilander.py`.

## Brainstorm Focus
- Emphasize mastery, efficiency, or awe-inspiring combos unlocked only at prime difficulty.
- Tie boosts to signature mechanics (unique resources, summons, weapon swaps, etc.).
- Ensure counters exist via timing, dispels, or resource denial so the fight remains interactive.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Explain what makes each idea “prime worthy” compared to the normal kit.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/hilander.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime Concepts

### Option 1: Perfect Fermentation (Recommended)
- Crit stacks build 50% faster (7.5% rate, 15% damage/stack)
- At 10+ stacks: Crits chain to nearest enemy (50% damage)
- At 20+ stacks: Crit creates persistent "Ferment Cloud" AoE zone
- Cloud applies half-strength crit buffs to allies in range
- No diminishing returns until 30 stacks

**Prime-Worthy:** Multi-target crits, zone creation, team utility.

### Option 2: Guaranteed Crits
- At 15 stacks: Next 3 hits guaranteed crit
- Consuming stacks grants "Perfectionist" buff: +100% crit damage for 2 turns
- Can bank multiple guaranteed crit windows

### Option 3: Overflow Mastery  
- Stack cap removed entirely
- Past 25 stacks: Gain "Overflow" state (permanent until crit)
- Overflow: Every hit has 25% chance to trigger bonus crit (doesn't consume stacks)
- Main crit consumes all stacks for massive damage

**Recommendations:** Perfect Fermentation for AoE, Guaranteed Crits for consistency.
