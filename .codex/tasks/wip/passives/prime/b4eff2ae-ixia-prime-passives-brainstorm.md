# Task: Brainstorm Prime Tier Tagged Passives for Ixia

## Background
Ixia's core moveset and lore live in `backend/plugins/characters/ixia.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/ixia.py`.

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
- Character plugin: `backend/plugins/characters/ixia.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime Concepts

### Titan Ascendant (Recommended)
- VIT→ATK conversion: 750% (up from 500%)
- VIT→HP conversion: 6× (up from 4×)
- Gain 0.5 VIT per damage dealt (not just taken)
- At 150 VIT: "True Titan" state
  - Size increase 200%
  - Immune to knockback/CC
  - Intimidation aura (-20% enemy ATK in range)
  - All attacks become AoE cleaves

### Adaptive Titan
- VIT bonuses adapt to combat situation:
  - High damage taken: Bonus DEF per VIT
  - High damage dealt: Bonus SPD per VIT
  - Low HP: Emergency VIT burst (+50 instant)

### Titan's Wrath
- Every 50 VIT: Unlock powerful ability
  - 50: Ground Slam (AoE stun)
  - 100: Seismic Roar (team buff)
  - 150: Titan's Judgment (execute below 20% HP enemies)

**Recommendations:** Titan Ascendant for power fantasy fulfillment.
