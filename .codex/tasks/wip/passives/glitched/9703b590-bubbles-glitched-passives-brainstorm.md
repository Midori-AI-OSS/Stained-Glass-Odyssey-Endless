# Task: Brainstorm Glitched Tier Tagged Passives for Bubbles

## Background
Bubbles's core moveset and lore live in `backend/plugins/characters/bubbles.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/bubbles.py`.

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
- Character plugin: `backend/plugins/characters/bubbles.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the glitched tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Glitched Concepts

### Option 1: Quantum Bubbles (Recommended)
**Fantasy Hook:** Glitched Bubbles exists in superposition, with burst timing becoming probabilistic and chaotic.

**Mechanics:**
- **Trigger:** `hit_landed`, random proc
- **Effect:**
  - Burst threshold becomes variable: 1-5 hits (rolled each stack application)
  - 25% chance per hit that bubble stack "quantum tunnels" to another random enemy
  - When burst triggers, 50% chance it triggers twice (double explosion)
  - 10% chance burst "collapses" harmlessly (no damage, stacks vanish)
  - Element rotation happens 2-3 times per turn instead of once (random timing)
- **Synergies:** Extreme unpredictability, high variance gameplay
- **Tuning Knobs:** Probability values, quantum tunnel range, double burst chance

**Glitch-Worthy Aspect:** Deterministic mechanic becomes chaotic and unpredictable.

**UI/Log Notes:**
- Stack counters flicker and change colors erratically
- Visual: Bubbles phases in/out, micro-bubbles teleport randomly
- Log: "Quantum superposition! Burst at {X} stacks!" (variable display)
- Log: "Bubble stack tunnels to {target}!"
- Glitch effects: scanlines, chromatic aberration on burst

**Counterplay:** Can't reliably predict bursts; focus on general damage reduction and positioning

**Risks:** Too random might feel unfair; ensure average burst rate stays balanced

---

### Option 2: Corrupted Overflow
**Fantasy Hook:** Glitched pressure system leaks energy erratically, causing chaotic side effects.

**Mechanics:**
- **Trigger:** Stack accumulation, turn_end
- **Effect:**
  - Bubble stacks randomly "overflow" to adjacent enemies each turn
  - Overflow amount: 1d3 stacks to 1-2 random nearby enemies
  - When any enemy reaches burst threshold via overflow:
    - 33% chance: Normal burst
    - 33% chance: Burst heals Bubbles instead of damage
    - 34% chance: Burst applies random debuff to Bubbles
  - Stacks can overflow to allies (if any), causing friendly fire bursts
- **Synergies:** Area-of-effect chaos, positioning critical
- **Tuning Knobs:** Overflow rate, effect probabilities, heal/debuff strength

**Glitch-Worthy Aspect:** Resource tracking corrupted, spreads unpredictably.

**UI/Log Notes:**
- Animated "leak" effects showing stacks jumping between targets
- Visual: Glitchy particle trails between characters
- Log: "Corrupted overflow! Stacks leak to {target}!"
- Log: "ERROR: Burst inverted - healing applied!"

**Counterplay:** Spread out to limit overflow chaining, cleanse stacks proactively

---

### Option 3: Volatile Membrane
**Fantasy Hook:** Glitched Bubbles' membrane stability fluctuates wildly, alternating between fragile and invulnerable.

**Mechanics:**
- **Trigger:** `damage_taken`, turn_start
- **Effect:**
  - Membrane state flips each turn: "Stable" ↔ "Unstable" (random starting state)
  - **Stable:** +50% defense, burst threshold +2, takes 50% less damage
  - **Unstable:** -50% defense, burst threshold -1, deals 100% more burst damage
  - 20% chance per hit to force immediate state flip (mid-turn)
  - Can't predict state changes; visual tells only after flip occurs
- **Synergies:** Timing-based strategy, adaptable burst patterns
- **Tuning Knobs:** State duration, stat modifiers, flip probability

**Glitch-Worthy Aspect:** Defense becomes unreliable, creates risk/reward timing windows.

**UI/Log Notes:**
- Bubbles alternates between crystalline (stable) and roiling (unstable) appearance
- State indicator: "MEMBRANE: STABLE" or "MEMBRANE: UNSTABLE"
- Log: "Membrane destabilizes!" / "Membrane crystallizes!"
- Glitch effect: Static/distortion during flip

**Counterplay:** Burst during unstable, defend during stable; track flip timing

---

### Option 4: Recursive Burst Loop
**Fantasy Hook:** Glitched burst logic creates infinite recursion, generating duplicate explosions.

**Mechanics:**
- **Trigger:** Bubble burst activation
- **Effect:**
  - Each burst has 40% chance to create "Echo Burst" 1 turn later at same location
  - Echo Bursts have 25% chance to create their own Echo
  - Maximum 3 generations of echoes (burst → echo → echo → echo)
  - Each echo deals 75% of previous generation's damage
  - All echoes apply 1 bubble stack to hit enemies (can trigger new burst cycle)
- **Synergies:** Creates delayed pressure waves, zone denial
- **Tuning Knobs:** Echo probability, damage falloff, generation limit

**Glitch-Worthy Aspect:** Single action spawns temporal anomalies, feedback loops.

**UI/Log Notes:**
- Ghostly bubble images linger at burst locations with countdown timers
- Visual: Echo bursts have inverted/negative colors
- Log: "ERROR: Burst recursion detected! Echo in {X} turns..."
- Glitch effect: Rewind/playback visual on echo detonation

**Counterplay:** Leave burst zones quickly, don't re-enter echo areas

**Risks:** Visual clutter with multiple echoes; limit active echoes per area

---

### Option 5: Element Corruption
**Fantasy Hook:** Glitched element system cycles through impossible combinations and anti-elements.

**Mechanics:**
- **Trigger:** `turn_start`, element rotation
- **Effect:**
  - 50% chance to gain "Corrupted Element" instead of normal type
  - Corrupted elements have inverted effects:
    - Fire → heals enemies hit, damages Bubbles
    - Ice → speeds up enemies instead of slow
    - Lightning → drains Bubbles' energy
    - Dark → illuminates, removes debuffs
  - 25% chance to gain "Null Element" (no damage type, bypasses all resistances)
  - 10% chance to gain ALL elements simultaneously (chaotic multi-effect)
- **Synergies:** High risk/reward, unpredictable combat flow
- **Tuning Knobs:** Corruption chance, effect severity, null element damage

**Glitch-Worthy Aspect:** Core mechanic inverted, attacks become unreliable.

**UI/Log Notes:**
- Corrupted elements show as inverted colors or glitch patterns
- Visual: Corrupted damage has reversed particle effects
- Log: "Element corruption! {Type} inverted!"
- Warning: "CORRUPTED ELEMENT ACTIVE - EFFECTS INVERTED"

**Risks:** Could be frustrating if too unpredictable; consider showing next element in advance

---

## Recommendations

**Primary Choice: Quantum Bubbles**
- Best captures pure chaos of glitch
- Maintains core burst mechanic while making it unpredictable
- Clear visual feedback for glitchy behavior
- Retains counterplay through general defensive strategies

**Alternative: Recursive Burst Loop**
- Less chaotic than quantum bubbles but still glitchy
- Creates interesting zone control and timing challenges
- More learnable patterns while still feeling corrupted

**Support Option: Volatile Membrane**
- If glitched needs periodic windows of vulnerability
- Adds timing skill to encounter
- Less random, more rhythmic chaos

**Avoid:**
- Element Corruption might be too punishing/frustrating
- Corrupted Overflow could create excessive friendly fire issues

**Glitch Design Philosophy:**
- Maintain readability despite chaos
- Provide visual/audio tells for state changes
- Keep core identity (burst-based) while corrupting the details
- Unpredictable but not unfair
