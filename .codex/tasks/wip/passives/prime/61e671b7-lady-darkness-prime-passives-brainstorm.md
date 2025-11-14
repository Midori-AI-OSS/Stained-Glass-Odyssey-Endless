# Task: Brainstorm Prime Tier Tagged Passives for LadyDarkness

## Background
LadyDarkness's core moveset and lore live in `backend/plugins/characters/lady_darkness.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/lady_darkness.py`.

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
- Character plugin: `backend/plugins/characters/lady_darkness.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime: Eternal Night (Recommended)
- Veil potency doubled (2× stealth/debuff strength), Shadow Banishment ability (remove enemy from combat for 2 turns), Eclipse duration extended (4 turns vs 2), Shadow clones gain full AI and 50% of original stats, Darkness spreads passively (enemy vision reduced globally)

## Boss: Void Empress
**Phase 1:** Enhanced veil + shadow clones
**Phase 2 (66%):** Darkness Spreads - arena lighting reduced, shadows autonomous
**Phase 3 (33%):** Eclipse Totality - all light fails, only shadows visible, constant debuffs
**Phase 4 (<15%):** Void Singularity - threatens existence erasure (DPS check or wipe)

## Glitched: Shadow Corruption
- Shadows become hostile entities (attack everyone), Veil inverts (highlights instead of conceals), Darkness damages allies randomly, Eclipse timing corrupted (instant/permanent/never), Shadow clones betray Lady Darkness
