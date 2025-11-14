# Task: Brainstorm Glitched Tier Tagged Passives for Carly

## Background
Carly's core moveset and lore live in `backend/plugins/characters/carly.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/carly.py`.

## Brainstorm Focus
- Introduce volatility, trade-offs, or corrupted resource loops that still stay fair to fight.
- Show how the glitch motif distorts existing abilities (timing errors, duplicate actions, stat flicker, etc.).
- Account for readability so players can learn to counter or exploit the glitch state.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Capture the glitch fantasy plus the risk/reward profile for each concept.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/carly.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the glitched tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Glitched Concepts

### Option 1: Corrupted Conversion (Recommended)
**Fantasy Hook:** Glitched stat conversion system malfunctions, causing chaotic swaps between offense and defense.

**Mechanics:**
- **Trigger:** `turn_start`, stat changes
- **Effect:**
  - Conversion direction randomizes each turn:
    - 50% chance: Normal (ATK→DEF)
    - 30% chance: Inverted (DEF→ATK)
    - 20% chance: Both freeze (no conversion)
  - Overcharge triggers randomly (10% chance/turn if 20+ stacks)
  - Overcharge state duration: 1-5 turns (random)
  - Stack decay/gain becomes erratic: ±2-8 stacks/turn randomly
  - 15% chance healing targets enemy instead of ally
- **Synergies:** Extreme volatility, unpredictable power swings
- **Tuning Knobs:** Randomization probabilities, ranges

**Glitch-Worthy:** Core mechanic becomes unreliable and chaotic.

**UI/Log Notes:**
- Stat bars flicker and swap positions
- Conversion arrow changes direction erratically
- Visual: Static/glitch effects on Carly's model
- Log: "ERROR: Conversion matrix corrupted! (ATK→DEF)" or "(DEF→ATK)"
- Log: "MALFUNCTION: Heal target lost!"

**Counterplay:** Unpredictable but averages out; focus on consistent DPS

**Risks:** Too random might feel unfair; ensure average stays balanced

---

### Option 2: Barrier Collapse Cascade
**Fantasy Hook:** Glitched barriers become unstable, exploding when they fail and damaging nearby units.

**Mechanics:**
- **Trigger:** Stack changes, damage taken
- **Effect:**
  - When losing 10+ stacks in single turn: Trigger "Barrier Collapse"
    - AoE damage to all nearby units (ally and enemy)
    - Damage = lost stacks × 10
    - Applies random status effect
  - Stacks decay unpredictably: 0-15 per turn
  - 25% chance barriers apply to enemies instead of allies
  - Overcharge triggers explosion every turn (self-damage)
- **Synergies:** Creates area hazard, friendly fire risk
- **Tuning Knobs:** Collapse threshold, damage multiplier, effect probabilities

**Glitch-Worthy:** Protective mechanic becomes dangerous to everyone.

**UI/Log Notes:**
- Barriers visually crack and spark before collapsing
- Explosion radius indicator
- Log: "CRITICAL FAILURE: Barrier collapse imminent!"
- Glitch effect: Barrier fragments scatter with static

**Counterplay:** Maintain distance from Carly, time attacks around collapses

---

### Option 3: Healing Flux
**Fantasy Hook:** Glitched healing algorithm becomes erratic, causing unpredictable health swings.

**Mechanics:**
- **Trigger:** Healing activations
- **Effect:**
  - Heal amount randomized: 0-200% of normal
  - 20% chance heal becomes damage
  - 15% chance heal affects all units in radius (friend and foe)
  - 10% chance heal creates "Flux Zone"
    - Zone alternates healing/damaging every turn
    - Lasts 3 turns
    - Max 2 zones active
  - Critical heals (>150%) grant temporary shield
- **Synergies:** High variance support, zone hazards
- **Tuning Knobs:** Randomization ranges, zone effects

**Glitch-Worthy:** Reliable sustain becomes gambling.

**UI/Log Notes:**
- Healing numbers display with static/glitch effect
- Flux zones pulse between green (heal) and red (damage)
- Log: "HEALING FLUX: Unstable output!"
- Log: "REVERSAL: Damage applied!"

**Open Questions:** Should flux zones persist if Carly is defeated?

---

### Option 4: Phase Desync
**Fantasy Hook:** Glitched Carly exists in multiple time states simultaneously, phasing between past/present/future.

**Mechanics:**
- **Trigger:** Automatic, time-based
- **Effect:**
  - Every 2-4 turns (random), Carly "phases"
  - **Past Phase:** Stats revert to turn 1 values
  - **Present Phase:** Normal stats
  - **Future Phase:** Stats as if 10 turns ahead
  - Phase lasts 1-2 turns
  - During phase: Actions may occur twice or not at all (50% each)
  - Stack count flickers between phase values
- **Synergies:** Temporal chaos, unpredictable power level
- **Tuning Knobs:** Phase frequency, duration, stat modifiers

**Glitch-Worthy:** Temporal instability, existence itself is glitched.

**UI/Log Notes:**
- Carly's model phases in/out with afterimages
- Stat displays show multiple values overlaid
- Log: "TEMPORAL ANOMALY: Phase shift to {past/present/future}"
- Visual: Scanline effect, color distortion

**Counterplay:** Burst during weak phases, survive strong phases

**Risks:** Very confusing; might need clear visual tells

---

### Option 5: Stack Integer Overflow
**Fantasy Hook:** Glitched stack counter overflows at high values, causing wraparound bugs.

**Mechanics:**
- **Trigger:** Stack thresholds
- **Effect:**
  - At 100 stacks: Overflow to -50 stacks (negative defense!)
  - At -50 stacks: Underflow to 75 stacks
  - Negative stacks grant ATK but reduce DEF dramatically
  - Overcharge can trigger at negative values (uses absolute value)
  - Random +20-30 stack jumps every 3-5 turns
- **Synergies:** Creates cycles of vulnerability and strength
- **Tuning Knobs:** Overflow thresholds, negative stack effects

**Glitch-Worthy:** Programming error made manifest.

**UI/Log Notes:**
- Stack counter displays corrupted values: "█##̷ STACKS"
- Visual: Model distorts at overflow point
- Log: "INTEGER OVERFLOW: Stack reset to {value}"

**Counterplay:** Track cycles, burst during negative stack windows

---

## Recommendations

**Primary: Corrupted Conversion**
- Directly corrupts core mechanic
- Maintains identity while adding chaos
- Learnable patterns despite randomness
- Multiple failure modes

**Alternative: Barrier Collapse Cascade**
- If glitched needs area denial
- Creates positioning challenges
- High impact visual feedback

**Interesting: Phase Desync**
- Most thematically glitched
- Temporal instability is very sci-fi
- Might be too complex

**Avoid: Stack Integer Overflow**
- Too punishing at overflow points
- Hard to communicate clearly
