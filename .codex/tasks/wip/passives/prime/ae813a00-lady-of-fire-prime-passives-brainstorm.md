# Task: Brainstorm Prime Tier Tagged Passives for LadyOfFire

## Background
LadyOfFire's core moveset and lore live in `backend/plugins/characters/lady_of_fire.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/lady_of_fire.py`.

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
- Character plugin: `backend/plugins/characters/lady_of_fire.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria [...]

##Prime: Eternal Flame - Momentum unlimited, self-burn immunity, phoenix resurrection, flame propagation (spreads to enemies)
##Boss: Inferno Incarnate - **P1:** Smolder(gradual). **P2(66%):** Blaze(fast). **P3(33%):** Inferno(constant). **P4(<15%):** Supernova(wipe threat)
##Glitched: Fire Chaos - Burns wrong targets (ally/self), momentum corrupted (negative/infinite), flames random (extinguish/explode)
