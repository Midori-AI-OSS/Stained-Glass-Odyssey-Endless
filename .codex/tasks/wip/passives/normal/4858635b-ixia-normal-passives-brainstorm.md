# Task: Brainstorm Normal Tier Tagged Passives for Ixia

## Background
Ixia's core moveset and lore live in `backend/plugins/characters/ixia.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/ixia.py`.

## Brainstorm Focus
- Lean into the character's existing kit loops, weapons, and stat hooks.
- Keep mechanics reliable and readable so they can anchor the rest of the tier variants.
- Spot opportunities for QoL or utility twists that feel unique to the character without power creeping boss/prime ideas.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Each option should mention what gameplay loop it reinforces for standard encounters.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/ixia.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Brainstormed Concepts

### Current Implementation: Tiny Titan (IMPLEMENTED)
**Mechanics:** 4× VIT→HP conversion, 500% VIT→ATK conversion, gains VIT on damage taken.
**Fantasy:** Small but mighty - grows stronger from adversity.

### Option 1: David vs Goliath
- Bonus damage vs larger enemies (+50% per size tier difference)
- Gain VIT faster when fighting stronger foes
- At 100 VIT: "Giant Slayer" mode - guaranteed crits vs bosses

### Option 2: Compact Power
- Higher VIT = smaller hitbox (evasion bonus)
- Stacking VIT reduces cooldowns (compression effect)
- Overload at 200 VIT: Temporary size increase + AoE attacks

### Option 3: Resilient Growth
- Damage taken converts to permanent VIT (10% of damage)
- Each death/revival grants +25 VIT permanently
- HP regen scales with VIT (1% max HP/10 VIT)

**Recommendations:** Current implementation strong. David vs Goliath adds fantasy flavor.

---

## Prime: Titan Ascendant
- VIT→ATK conversion improved to 750%
- Gain VIT from all damage (dealt and taken)
- At 150 VIT: Unlock "True Titan" - immune to knockback, +100% size, intimidation aura

## Boss: Colossus Awakening
- **Phase 1:** Normal + passive VIT gain
- **Phase 2 (50% HP):** Size doubles, VIT→ATK = 1000%, AoE all attacks
- **Phase 3 (25% HP):** "Kaiju Mode" - screen-filling size, environmental damage

## Glitched: Size Glitch
- Size fluctuates randomly (tiny→huge each turn)
- VIT conversions invert randomly (ATK→VIT sometimes)
- Collision detection errors cause teleportation
