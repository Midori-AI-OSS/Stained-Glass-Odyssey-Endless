# Task: Brainstorm Boss Tier Tagged Passives for Bubbles

## Background
Bubbles's core moveset and lore live in `backend/plugins/characters/bubbles.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/bubbles.py`.

## Brainstorm Focus
- Dial up threat pacing via enrages, arena control, multi-phase cues, or punishing counterplay.
- Respect the character fantasy—make the boss feel like an ultimate expression of their personality.
- Consider survivability, anti-burst safeguards, and memorable telegraphs the UI/logs can surface.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Highlight how each idea creates a set-piece moment or new failure condition for parties.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/bubbles.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the boss tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Boss Concepts

### Option 1: Pressure Critical (Recommended)
**Fantasy Hook:** Boss Bubbles builds catastrophic pressure throughout the fight, threatening total arena saturation.

**Mechanics:**
- **Trigger:** `turn_start`, `hit_landed`, phase thresholds
- **Effect:**
  - Bubbles gains "Overpressure" stacks throughout combat (1 per turn, 2 per burst)
  - At 10/20/30 Overpressure: Arena-wide pressure wave
    - 10: Minor damage, applies 1 bubble stack to all enemies
    - 20: Moderate damage, applies 2 bubble stacks, random status effects
    - 30: Heavy damage, triggers all bubble bursts simultaneously
  - Overpressure reduces by 5 when hit with dispels or specific elements
  - **Phase Shift at 50% HP:** Pressure buildup accelerates (2x rate)
- **Synergies:** Creates urgency, rewards pressure management
- **Tuning Knobs:** Stack thresholds, wave damage, phase trigger HP

**Boss-Worthy Aspect:** Creates multi-phase encounter with escalating threat and DPS check.

**UI/Log Notes:**
- Large pressure gauge visible to all players: "OVERPRESSURE: 15/30"
- Warning at 25+: "CRITICAL PRESSURE BUILDING!"
- Screen shake and sound effects at each threshold
- Log: "The chamber trembles with overwhelming pressure!"

**Counterplay:** Dispel mechanics, burn down before thresholds, manage bubble stacks carefully

---

### Option 2: Hydrostatic Arena Control
**Fantasy Hook:** Boss Bubbles floods the battlefield with pressurized zones that alter combat dynamics.

**Mechanics:**
- **Trigger:** `turn_start`, bubble burst, HP thresholds
- **Effect:**
  - Each burst creates permanent "Pressure Zone" at location
  - Zones have stacking effects:
    - 1 zone: -10% movement speed for enemies in zone
    - 2 zones: -20% speed + periodic damage ticks
    - 3+ zones: -30% speed + damage + bubble stack application
  - At 75%/50%/25% HP, Bubbles triggers "Flood Surge"
    - Expands all zones by 50%, merges overlapping zones
    - Merged zones apply double effects
  - Zones persist entire fight, max 8 active
- **Synergies:** Territory control, zone denial, positioning challenges
- **Tuning Knobs:** Zone size, effect strength, max zones, persistence

**Boss-Worthy Aspect:** Battlefield becomes increasingly hazardous, rewarding positioning and mobility.

**UI/Log Notes:**
- Glowing cyan circles showing pressure zones
- Zone indicators show stack count and effects
- Log: "Flood Surge! The arena is consuming!"
- Warning: "Standing in {X} pressure zones!"

**Counterplay:** Maintain mobility, fight at edges, cleanse effects

---

### Option 3: Adaptive Membrane (Survival Mechanic)
**Fantasy Hook:** Boss Bubbles' membrane adapts to damage, becoming harder to burst down.

**Mechanics:**
- **Trigger:** `damage_taken`, HP thresholds
- **Effect:**
  - Tracks most-used damage type against Bubbles
  - Gains +5% resistance to that type per hit (max +50%)
  - At 30% resistance, gains immunity for 2 turns, then resets to 0%
  - Swaps damage vulnerability: Takes +25% from opposite element
  - **Enrage at 25% HP:** Resistance builds twice as fast
- **Synergies:** Punishes single-element strategies, requires adaptability
- **Tuning Knobs:** Resistance rate, immunity threshold, enrage trigger

**Boss-Worthy Aspect:** Requires diverse damage types, creates micro-puzzles during encounter.

**UI/Log Notes:**
- Visual membrane color shifts toward resisted element
- Resistance bar shows current adaptation progress
- Log: "Bubbles' membrane adapts to {element}! (+{X}% resistance)"
- Warning: "Immunity imminent! Switch damage types!"

**Risks:** Could frustrate if players lack element variety; ensure all classes have options.

---

### Option 4: Burst Barrage (Aggressive Scaling)
**Fantasy Hook:** Boss Bubbles releases overwhelming volleys of satellite bubbles that saturate the battlefield.

**Mechanics:**
- **Trigger:** `turn_start`, combat duration, HP thresholds
- **Effect:**
  - Every 3 turns, Bubbles summons 3-5 "Satellite Bubbles" (mini-summons)
  - Satellites have low HP but explode on death, applying bubble stacks
  - Satellites actively seek and attack nearest target
  - **Phase 2 (50% HP):** Summon rate increases to every 2 turns
  - **Phase 3 (25% HP):** Satellites become untargetable, explode after 2 turns
- **Synergies:** Creates add management, area control, pressure management
- **Tuning Knobs:** Summon frequency, satellite HP, explosion damage

**Boss-Worthy Aspect:** Multi-threat encounter, tests add management and prioritization.

**UI/Log Notes:**
- Satellite counter: "Satellites: 5 active"
- Countdown timers on untargetable satellites
- Log: "Bubbles releases a swarm of satellites!"
- Visual: Smaller bubbles orbiting boss, glowing brighter before explosion

**Counterplay:** AoE for satellites, CC to slow approach, high priority targeting

---

### Option 5: Tidal Momentum (Snowball Pressure)
**Fantasy Hook:** Boss Bubbles' momentum builds with each successful burst, creating runaway threat if not checked.

**Mechanics:**
- **Trigger:** Bubble burst activations
- **Effect:**
  - Each burst grants "Tidal Stack" (+5% damage, +5% action speed, stacking)
  - Stacks persist throughout combat (no decay)
  - At 10 stacks: Unlock "Tsunami Mode"
    - Burst threshold reduced to 1 hit
    - All bursts trigger chain reactions (like prime)
    - +50% damage and speed
  - Stacks reset to 0 if Bubbles doesn't burst for 5 consecutive turns
- **Synergies:** Punishes passive play, rewards pressure management
- **Tuning Knobs:** Stack bonuses, stack loss condition, Tsunami threshold

**Boss-Worthy Aspect:** Creates soft enrage timer, rewards aggressive counterplay.

**UI/Log Notes:**
- Tidal gauge showing stack buildup
- Visual: Bubbles grows larger and glows brighter with stacks
- Log: "Tidal force building! ({X}/10 stacks)"
- Warning at 8+: "TSUNAMI MODE IMMINENT!"

**Counterplay:** Force reset by preventing bursts (kiting, shields), burst down before Tsunami

---

## Recommendations

**Primary Choice: Pressure Critical + Hydrostatic Arena Control (Combined)**
- Combine overpressure mechanic with zone control for multi-layered boss fight
- Pressure gauge creates urgency, zones create positioning challenges
- Multiple failure conditions (overpressure threshold, zone saturation)
- Strong visual clarity and counterplay options

**Alternative: Adaptive Membrane + Burst Barrage**
- If boss needs more survivability and complexity
- Tests player adaptability and multi-tasking
- More mechanical than pressure-based

**Design Philosophy:**
- Boss Bubbles should feel like fighting an elemental force of nature
- Inevitable pressure buildup = time limit feel
- Zone control = environmental hazard
- Multiple concurrent threats without being unfair
