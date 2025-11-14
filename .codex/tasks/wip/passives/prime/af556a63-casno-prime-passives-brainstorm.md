# Task: Brainstorm Prime Tier Tagged Passives for Casno

## Background
Casno's core moveset and lore live in `backend/plugins/characters/casno.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/casno.py`.

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
- Character plugin: `backend/plugins/characters/casno.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime: Phoenix Ascendant (Recommended)
- Healing magnitude doubled (2× HoT ticks)
- Relaxed momentum builds 50% faster
- At max relaxation: Unlock "Eternal Flame" ability
  - Party-wide revive (once per combat)
  - All allies gain phoenix blessing (survive lethal hit with 1 HP, once)
  - Flames become self-sustaining (no momentum loss when attacking)
- Resurrection applies full HP restoration (not partial)

## Prime: Undying Will
- Cannot die while relaxed momentum active (minimum 1 HP)
- Taking lethal damage consumes all momentum for full heal
- Flames grow stronger with each near-death (stacking burn aura)

**Recommendations:** Phoenix Ascendant for dramatic team-save moments.
