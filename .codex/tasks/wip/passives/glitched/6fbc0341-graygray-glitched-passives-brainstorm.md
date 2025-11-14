# Task: Brainstorm Glitched Tier Tagged Passives for Graygray

## Background
Graygray's core moveset and lore live in `backend/plugins/characters/graygray.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/graygray.py`.

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
- Character plugin: `backend/plugins/characters/graygray.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the glitched tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Glitched Concepts

### Option 1: Paradox Counter (Recommended)
**Fantasy Hook:** Glitched counter timing becomes non-linear, triggering before/after/during attacks unpredictably.

**Mechanics:**
- 33% chance counter triggers BEFORE taking damage (preemptive)
- 33% chance normal counter AFTER damage
- 34% chance counter triggers on random enemy instead of attacker
- Stack gains randomized: 0-3 per hit
- Burst threshold varies: 30-70 stacks (rolled each burst)
- Counter damage: 50%-200% of normal (random per counter)

**Glitch-Worthy:** Temporal causality broken, completely unpredictable timing.

**UI/Log Notes:**
- Counter effects have inverted/glitched visuals
- Log: "TEMPORAL ANOMALY: Counter paradox!"
- Static effects on counter animations

**Counterplay:** Expect chaos, focus on consistent DPS rather than burst timing.

---

### Option 2: Stack Corruption
**Fantasy Hook:** Glitched stack counter becomes volatile, randomly spiking or crashing.

**Mechanics:**
- Stacks display as corrupted values: "##?" or "ERR"
- Random events each turn:
  - 25%: +20-40 stacks instantly
  - 25%: Lose 10-30 stacks
  - 25%: Stacks freeze (no gain/loss)
  - 25%: Double stack gain rate
- Burst can trigger at ANY stack value (10% chance/turn if 10+ stacks)
- ATK buff calculation uses corrupted formula (sometimes negative)

**Glitch-Worthy:** Core resource tracking completely unreliable.

**UI/Log Notes:**
- Stack counter flickers and shows garbled numbers
- Log: "STACK OVERFLOW ERROR"

---

### Option 3:反射錯誤 (Reflection Error)
**Fantasy Hook:** Glitched counters reflect back on Graygray himself or allies.

**Mechanics:**
- 40% chance counter hits intended target
- 30% chance counter hits random ally
- 30% chance counter hits Graygray (self-damage)
- Misdirected counters still build stacks
- Bursts can chain to anyone (friend or foe)
- "Error Cascade": At 75 stacks, burst hits ALL units (team-wipe risk)

**Glitch-Worthy:** Friendly fire, self-harm, ultimate chaos.

**UI/Log Notes:**
- Counter projectiles ricochet erratically
- Log: "TARGETING ERROR: Counter misdirected!"

---

## Recommendations
**Primary: Paradox Counter** - Maintains identity while adding temporal chaos.
**Risky: Reflection Error** - High chaos, might feel unfair with team damage.
