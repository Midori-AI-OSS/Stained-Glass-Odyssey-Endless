# Task: Brainstorm Prime Tier Tagged Passives for Bubbles

## Background
Bubbles's core moveset and lore live in `backend/plugins/characters/bubbles.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/bubbles.py`.

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
- Character plugin: `backend/plugins/characters/bubbles.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the prime tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Prime Concepts

### Option 1: Cascading Detonation (Recommended)
**Fantasy Hook:** Prime Bubbles' bursts trigger chain reactions across multiple enemies, creating cascading explosions.

**Mechanics:**
- **Trigger:** `hit_landed`, bubble burst activation
- **Effect:**
  - Reduce burst threshold from 3 hits to 2 hits
  - When burst triggers on primary target:
    - Deal AoE damage (150% of normal burst) to enemies within radius
    - Enemies hit gain 1 bubble stack instantly
    - If any enemy reaches burst threshold, chain another detonation
  - Maximum 5 chain bounces per trigger
- **Synergies:** Multiplies value of focused attacks, rewards grouped enemies
- **Tuning Knobs:** Chain limit, AoE radius, damage scaling per chain

**Prime-Worthy Aspect:** Transforms single-target burst into room-clearing cascades, mastery of pressure dynamics.

**UI/Log Notes:**
- Chain counter appears during cascade: "Chain x2! x3! x4!"
- Visual: Lightning-like connections between bursting bubbles
- Log: "Cascading Detonation! {X} chains!"

**Counterplay:** Spread enemy positioning, dispel bubble stacks, interrupt with CC

---

### Option 2: Perfect Pressure Control
**Fantasy Hook:** Mastery over internal pressure allows Bubbles to selectively detonate bubbles for strategic advantage.

**Mechanics:**
- **Trigger:** `turn_start`, `manual_activation` (could be tied to Ultimate gauge)
- **Effect:**
  - Bubbles can choose to detonate ANY target with at least 1 stack (not just at 3)
  - Early detonation (1 stack): 33% damage, applies slow
  - Mid detonation (2 stacks): 66% damage, applies vulnerability
  - Full detonation (3+ stacks): 100% damage + AoE splash
  - Gain +10% damage on all attacks for 2 turns after any detonation
- **Synergies:** Adds tactical depth, combo potential with debuffs
- **Tuning Knobs:** Partial detonation damage %, buff duration, cooldowns

**Prime-Worthy Aspect:** Adds player agency and strategic timing, shows mastery over basic mechanic.

**UI/Log Notes:**
- Glowing indicator on enemies showing "Ready to Burst" even at partial stacks
- Pop-up: "Early Burst Available!"
- Log: "Bubbles triggers Pressure Release! (X% power)"

**Open Questions:** Should early detonation consume all stacks or allow rebuilding? Cooldown needed?

---

### Option 3: Prismatic Overload
**Fantasy Hook:** Prime Bubbles' elemental mastery manifests as simultaneous multi-element attacks.

**Mechanics:**
- **Trigger:** `turn_start`, `hit_landed`
- **Effect:**
  - Instead of single element rotation, Bubbles simultaneously attunes to 2-3 random elements
  - Each hit applies damage of ALL attuned elements (reduced to 60% each)
  - Bubble bursts deal damage of all attuned types
  - Enemies hit by 3+ different element types gain "Prismatic Weakness" (-15% all resistances)
- **Synergies:** Bypasses single-element resistances, applies multiple status effects
- **Tuning Knobs:** Element count, damage reduction per element, weakness strength

**Prime-Worthy Aspect:** Elevates elemental chaos to mastery, makes element RNG an advantage.

**UI/Log Notes:**
- Bubbles displays multiple color swirls simultaneously
- Log: "Prismatic Overload! {Fire + Lightning + Ice}"
- Visual: Multi-colored explosion effects

**Risks:** Complex to implement, may feel overwhelming. Consider limiting to 2 elements for clarity.

---

### Option 4: Effervescent Regeneration
**Fantasy Hook:** Prime Bubbles' bursts release healing mist that sustains allies through extended combat.

**Mechanics:**
- **Trigger:** Bubble burst activation
- **Effect:**
  - Each burst creates a "Healing Mist" zone at detonation point
  - Zone lasts 3 turns, heals allies for 5% max HP per turn while standing in it
  - Multiple zones stack healing (max 3 zones active)
  - Bubbles gains burst cooldown reduction per ally healed
- **Synergies:** Adds support utility, rewards positioning
- **Tuning Knobs:** Heal %, zone duration, zone size, stack limit

**Prime-Worthy Aspect:** Transforms offensive mechanic into support tool, shows battle mastery.

**UI/Log Notes:**
- Glowing cyan puddles on battlefield showing healing zones
- HP floaties showing heal ticks
- Log: "Healing Mist flows from the burst!"

**Open Questions:** Should zones heal enemies too? Might add strategic depth but could backfire.

---

### Option 5: Hypercompression
**Fantasy Hook:** Prime pressure control allows Bubbles to compress energy, accelerating combat tempo.

**Mechanics:**
- **Trigger:** `turn_end`, combat duration
- **Effect:**
  - For every 2 bubble bursts triggered, gain +5% action speed (stacking)
  - At 5 total bursts in combat, unlock "Hypercompressed State":
    - Burst threshold reduced to 1 hit
    - Bursts deal 50% damage but trigger twice as fast
    - State lasts until combat ends
  - Max +25% action speed
- **Synergies:** Rewards aggressive play, snowball mechanic
- **Tuning Knobs:** Burst count threshold, speed bonus, state duration

**Prime-Worthy Aspect:** Accelerating combat flow, momentum mastery.

**UI/Log Notes:**
- Compression gauge fills with each burst
- Bubbles vibrates/pulsates faster in Hypercompressed State
- Log: "Hypercompression achieved! Rapid-fire bursts!"

**Risks:** Snowball potential very high; ensure boss encounters can counter or reset.

---

## Recommendations

**Primary Choice: Cascading Detonation**
- Best captures "prime mastery" fantasy
- Clear visual payoff (chain explosions)
- Has natural counterplay (positioning)
- Scales existing mechanic without adding complexity

**Alternative: Perfect Pressure Control**
- Adds tactical depth
- Rewards skilled timing
- More interactive for player
- May require UI changes for manual activation

**Support Option: Effervescent Regeneration**
- If Bubbles needs survivability or team utility
- Makes prime encounters feel distinct
- Adds strategic positioning element

**Avoid for Prime:**
- Prismatic Overload might be too chaotic/confusing
- Hypercompression risks runaway snowball without careful tuning
