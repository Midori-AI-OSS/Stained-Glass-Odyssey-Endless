# Task: Brainstorm Prime Tier Tagged Passives for Mezzy

## Background
Mezzy's core moveset and lore live in `backend/plugins/characters/mezzy.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/mezzy.py`.

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
- Character plugin: `backend/plugins/characters/mezzy.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime: Insatiable Appetite (Recommended)
- Absorption rate doubled (2× damage reduction, 2× stat siphon), Siphoned stats become permanent (don't decay), At 100 total absorbed stats: Unlock "Glut Mode" (3 turns: invulnerable + 100% damage reflection + size increase), Can willingly absorb ally buffs for emergency power spike, Enemy debuffs also absorbed and converted to buffs

## Prime: Adaptive Metabolism
- Absorption adapts to damage type (resist what's absorbed), Converts absorbed damage to healing (50% conversion), Siphon rate increases with missing HP (desperate hunger), Ultimate: "Devour" ability (instant-kill enemies below 15% HP, gain all their stats)

**Recommendations:** Insatiable Appetite for power fantasy scaling.
