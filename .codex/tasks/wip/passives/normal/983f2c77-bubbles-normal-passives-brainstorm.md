# Task: Brainstorm Normal Tier Tagged Passives for Bubbles

## Background
Bubbles's core moveset and lore live in `backend/plugins/characters/bubbles.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/bubbles.py`.

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
- Character plugin: `backend/plugins/characters/bubbles.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the normal tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Concepts

### Current Implementation: Bubble Burst (IMPLEMENTED)
**Fantasy Hook:** Bubbles builds up pressure with each hit, exploding in chain reactions after landing 3 hits on the same target.

**Mechanics:**
- **Trigger:** `turn_start` (random element rotation) and `hit_landed` (stack accumulation)
- **Effect:** 
  - Turn start: Rotate to random damage type from ALL_DAMAGE_TYPES
  - Hit landed: Add bubble stack to target (max 20 shown, 3 for burst)
  - At 3 stacks: Trigger area burst damage, reset stacks
- **Synergies:** Works with any damage-dealing abilities; random element adds unpredictability
- **Tuning Knobs:** Stack threshold (currently 3), area damage multiplier, stack cap display

**UI/Log Notes:** 
- Display bubble stacks on enemies as numbers (0-3 before burst, overflow shown up to 20)
- Log message: "{Bubbles} triggers Bubble Burst on {target}!"
- Visual: Rainbow cascade effect on burst

**Gameplay Loop:** Encourages focused targeting (3 hits on same enemy) while maintaining element variety. Creates satisfying burst moments without being too predictable.

---

### Option 1: Pressure Buildup (Alternative Approach)
**Fantasy Hook:** Each consecutive hit on the same target increases internal pressure, granting escalating damage bonuses.

**Mechanics:**
- **Trigger:** `hit_landed`
- **Effect:**
  - Track consecutive hits per target
  - Grant stacking damage buff: +5% per hit (max 5 stacks = +25%)
  - Reset if switching targets or missing
  - At max stacks, next hit deals bonus splash damage to adjacent enemies
- **Synergies:** Rewards target focus, pairs with multi-hit abilities
- **Tuning Knobs:** Damage % per stack, max stacks, splash radius

**UI/Log Notes:**
- Stack counter on Bubbles showing pressure level (1-5)
- Color shift: Blue→Cyan→White as pressure builds
- Log: "Bubbles' pressure builds! (+{X}% damage)"

**Open Questions:** Should pressure decay over time or only reset on target switch?

---

### Option 2: Bubble Shield Formation (Defensive Utility)
**Fantasy Hook:** Bubbles generates protective micro-bubbles that absorb incoming damage.

**Mechanics:**
- **Trigger:** `turn_start`, `damage_taken`
- **Effect:**
  - Turn start: Generate 1-3 shield bubbles
  - Each bubble absorbs one hit (up to X damage)
  - When bubble pops, splash damage to attacker (25% of absorbed damage)
  - Max 5 bubbles active at once
- **Synergies:** Adds survivability, creates counterattack opportunities
- **Tuning Knobs:** Bubbles per turn, absorption cap, splash damage %

**UI/Log Notes:**
- Display bubble count as shield icons around Bubbles
- Pop sound and visual sparkle on absorption
- Log: "Bubbles' shield absorbs the attack! (X bubbles remaining)"

**Risks:** Might make Bubbles too tanky for normal tier; consider reducing absorption cap

---

### Option 3: Chromatic Cascade (Elemental Chain)
**Fantasy Hook:** Cycling through elements creates resonance effects when matching damage types in sequence.

**Mechanics:**
- **Trigger:** `turn_start`, `damage_dealt`
- **Effect:**
  - Track last 3 damage types used
  - If 3 different types: Bonus "prismatic" damage on next hit
  - If 3 same types: Temporary +15% damage of that type
  - Element rotates each turn (existing mechanic)
- **Synergies:** Encourages tactical element diversity or specialization
- **Tuning Knobs:** Sequence length, bonus damage amounts, duration

**UI/Log Notes:**
- Visual trail showing last 3 elements used (colored orbs)
- Log: "Chromatic Cascade: Prismatic burst!" or "Elemental resonance achieved!"

**Open Questions:** Does this conflict with existing random element rotation? Should player have control over element choice?

---

### Option 4: Overflow Momentum (Sustained Combat Bonus)
**Fantasy Hook:** Extended combat causes Bubbles' energy to overflow, increasing action economy.

**Mechanics:**
- **Trigger:** `turn_end`, combat duration tracking
- **Effect:**
  - For every 3 consecutive turns in combat, gain +1% action speed
  - For every 10 hits landed total, reduce ultimate cooldown by 1
  - Bonuses persist until combat ends
  - Max +10% speed, max -5 cooldown reduction
- **Synergies:** Rewards staying power, scales with longer fights
- **Tuning Knobs:** Turn threshold, speed/cooldown amounts, caps

**UI/Log Notes:**
- Counter showing "Momentum: X turns / Y hits"
- Visual: Bubbles glows brighter, micro-bubbles spin faster
- Log: "Bubbles' overflow accelerates!"

**Risks:** Might make long fights too easy; consider dimishing returns

---

## Recommendations
The current **Bubble Burst** implementation is solid for normal tier:
- Clear, readable mechanic (3-hit burst)
- Fits character fantasy perfectly
- Has counterplay (spread damage to avoid stacks)
- Room to escalate in higher tiers (more stacks, faster buildup, etc.)

**Suggested refinements:**
1. Add visual feedback for stack accumulation (bubble particles growing on enemy)
2. Consider making burst radius slightly larger for more impact
3. Log messages could be more flavorful ("Pop! Pop! POP!")

**For higher tiers to explore:**
- Prime: Multi-target burst chains, lower stack threshold
- Boss: Burst creates lingering hazard zones
- Glitched: Random burst triggers, chaotic element swaps mid-burst
