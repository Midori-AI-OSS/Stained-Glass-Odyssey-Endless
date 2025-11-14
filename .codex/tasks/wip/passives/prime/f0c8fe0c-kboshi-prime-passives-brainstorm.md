# Task: Brainstorm Prime Tier Tagged Passives for Kboshi

## Background
Kboshi's core moveset and lore live in `backend/plugins/characters/kboshi.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/kboshi.py`.

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
- Character plugin: `backend/plugins/characters/kboshi.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Prime Concepts

### Harmonic Convergence (Recommended)
- Dual element attunement (cycle 2 elements/turn)
- Damage applies both element types simultaneously
- HoT stacks build 50% faster
- Perfect Flux bonus: Cycle through all 6 unique elements→unlock "Prismatic Overload"
  - All elements active simultaneously for 2 turns
  - +200% damage, rainbow visual effect
  - HoT becomes supercharged regen

### Element Mastery
- Choose element each turn (remove randomness)
- Repeated element gains stacking bonus (+15% dmg/turn, max +75%)
- Switching breaks streak but grants burst damage
- Ultimate control vs random chaos

### Resonant Amplification
- Matching ally elements grants team buff
- Opposing enemy elements grant resistance
- At 10 element matches: Team-wide elemental infusion

**Recommendations:** Harmonic Convergence for prismatic power fantasy.
