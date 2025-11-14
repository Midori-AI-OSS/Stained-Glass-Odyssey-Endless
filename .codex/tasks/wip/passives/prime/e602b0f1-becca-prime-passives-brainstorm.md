# Task: Brainstorm Prime Tier Tagged Passives for Becca

## Background
Becca's core moveset and lore live in `backend/plugins/characters/becca.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/becca.py`.

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
- Character plugin: `backend/plugins/characters/becca.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime: Spirit Sanctuary (Recommended)
- Summon 2-3 jellyfish simultaneously (up from 1), Pets revive once automatically when killed, Bond bonuses doubled (+50% stats from pets instead of +25%), "Jellyfish Storm" unlocked (summon swarm of 5 temporary weak pets for AoE coverage)

## Prime: Eternal Companions
- Pets become permanent (don't despawn), Gain new pet type every 3 turns (variety), Bond stacks infinitely, At 10 total pets: "Aquarium Mode" (battlefield becomes underwater zone, all allies gain swim buffs)

**Recommendations:** Spirit Sanctuary for manageable pet scaling.
