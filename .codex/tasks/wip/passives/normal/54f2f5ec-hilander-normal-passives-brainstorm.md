# Task: Brainstorm Normal Tier Tagged Passives for Hilander

## Background
Hilander's core moveset and lore live in `backend/plugins/characters/hilander.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/hilander.py`.

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
- Character plugin: `backend/plugins/characters/hilander.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the normal tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Concepts

### Current Implementation: Critical Ferment (IMPLEMENTED)
**Fantasy Hook:** Hilander ferments critical strike potential with each hit, releasing devastating crits before starting over.

**Mechanics:**
- Gain stacks on hit: +5% crit rate, +10% crit damage per stack
- Stacks accumulate indefinitely (soft diminishing at 20+)
- On landing crit: Consume all stacks for amplified damage, reset to 0
- Crit damage scales with consumed stacks
- Aftertaste effect: Lingering stat modifiers after crit

**UI/Log Notes:**
- Pips display up to 5 stacks, then numeric
- Visual: Fermentation bubbles/glow intensifies
- Log: "Critical Ferment released!"

**Gameplay Loop:** Build-release cycle, timing crits for maximum impact, risk/reward of holding stacks.

---

### Option 1: Volatile Batch
**Fantasy Hook:** Fermentation becomes unstable at high stacks, risking premature detonation.

**Mechanics:**
- At 15+ stacks: 10% chance per hit to auto-crit (uncontrolled release)
- At 20+ stacks: Chance increases 5% per stack
- Voluntary early release grants bonus effects based on stack count
- Controlled releases add temporary "Mastery" buff

**UI/Log Notes:**
- Instability indicator at high stacks
- Visual: Bubbling/shaking at high fermentation

---

### Option 2: Dual Fermentation
**Fantasy Hook:** Hilander maintains two separate ferment batches for different tactical options.

**Mechanics:**
- Track two independent stack pools (offensive/utility)
- Offensive: Current crit stacking
- Utility: Defensive stacks (dodge/mitigation per stack)
- Choose which pool to consume on crit
- Consuming both grants fusion bonus

**UI/Log Notes:**
- Two separate pip displays
- Different visual colors for each type

---

### Option 3: Shared Brew
**Fantasy Hook:** Hilander's fermentation benefits nearby allies with splash effects.

**Mechanics:**
- Allies in range gain 25% of Hilander's crit bonuses
- When Hilander crits, allies get mini-burst effect
- Consuming stacks heals nearby allies
- Synergy: More allies = faster fermentation

**UI/Log Notes:**
- Aura effect showing brew sharing
- Log: "Shared Brew empowers the party!"

---

## Recommendations
**Current Implementation Strong:** Build-release cycle creates tactical depth, unlimited stacking with soft cap balances well.
**For Higher Tiers:**
- Prime: Faster stacking, multi-target crits
- Boss: Forced release phases, crit cascades
- Glitched: Random stack gains/losses, unexpected crits
