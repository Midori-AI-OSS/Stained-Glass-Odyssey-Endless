# Task: Brainstorm Prime Tier Tagged Passives for Ryne

## Background
Ryne's core moveset and lore live in `backend/plugins/characters/ryne.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/ryne.py`.

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
- Character plugin: `backend/plugins/characters/ryne.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime: Cosmic Equilibrium (Recommended)
- Balance window widened (40-60% vs 45-55%), Equilibrium buffs apply team-wide (+30% all stats when balanced), "Redistribute" ability: Force HP balance across all allies (cooldown), Perfect Balance (exactly 50/50): "Time Dilation" (team gains bonus turn), Penalty for imbalance reduced (−10% vs −20%)

## Prime: Fate Weaver
- Can set custom balance threshold (choose target %), Imbalance powers offensive abilities (scales with difference), "Tip the Scales" ultimate: Instantly swap party/enemy HP totals (once per combat)

**Recommendations:** Cosmic Equilibrium for team utility and perfect balance fantasy.
