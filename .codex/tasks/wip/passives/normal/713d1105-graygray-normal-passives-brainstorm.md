# Task: Brainstorm Normal Tier Tagged Passives for Graygray

## Background
Graygray's core moveset and lore live in `backend/plugins/characters/graygray.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/graygray.py`.

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
- Character plugin: `backend/plugins/characters/graygray.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the normal tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Concepts

### Current Implementation: Counter Maestro (IMPLEMENTED)
**Fantasy Hook:** Graygray retaliates after every hit, building attack power and unleashing devastating bursts.

**Mechanics:**
- **Trigger:** `damage_taken`
- **Effect:**
  - Gain 1 counter stack per hit received
  - Grant permanent ATK buff: +5% per stack (first 50), +2.5% per stack (50+)
  - At 50 stacks: Unleash burst counter dealing max HP damage to attacker
  - Burst consumes 50 stacks, can chain multiple bursts
  - Brief mitigation buff after each counter
- **Synergies:** Rewards taking damage, scales infinitely with diminishing returns
- **Tuning Knobs:** Stack threshold (50), ATK% per stack, burst damage, soft cap point

**UI/Log Notes:**
- Stack counter displays current counter stacks
- Visual: Sword aura intensifies with stacks
- Log: "Counter Maestro Burst!" on 50-stack trigger

**Gameplay Loop:** Tank-style counterattacker who becomes more dangerous the more he's hit. Risk/reward of intentionally tanking.

---

### Option 1: Riposte Timing
**Fantasy Hook:** Perfect timing on counters grants bonus effects and critical strikes.

**Mechanics:**
- **Trigger:** `damage_taken`, timing window
- **Effect:**
  - Normal counters deal base damage
  - "Perfect" counter (damaged within 0.5s of last action): 2× damage + crit
  - Track perfect counter streak (resets on miss)
  - At 3-streak: Next attack guaranteed crit
  - At 5-streak: AoE counter (hits all nearby enemies)
- **Synergies:** Skill-based timing, rewards aggression
- **Tuning Knobs:** Perfect window duration, streak bonuses

**UI/Log Notes:**
- "PERFECT!" flash on perfect counter
- Streak counter visible
- Log: "Perfect Riposte! Streak: {X}"

**Open Questions:** Can perfect timing be learned/predicted?

---

### Option 2: Defensive Stance Cycling
**Fantasy Hook:** Graygray cycles between aggressive and defensive postures, gaining different counter effects.

**Mechanics:**
- **Trigger:** `turn_start`, manual toggle
- **Effect:**
  - **Aggressive Stance:** Counters deal +50% damage, take +25% damage
  - **Defensive Stance:** Counters deal -25% damage, take -50% damage
  - Stance auto-switches every 3 turns OR manually via ability
  - Counter stacks build faster in aggressive, slower in defensive
- **Synergies:** Tactical positioning, phase management
- **Tuning Knobs:** Stance durations, damage modifiers

**UI/Log Notes:**
- Stance indicator: Red (aggressive) or Blue (defensive)
- Visual: Sword position changes with stance
- Log: "Graygray shifts to {stance}!"

---

### Option 3: Vengeance Mark
**Fantasy Hook:** Graygray marks enemies who damage him, dealing escalating revenge damage.

**Mechanics:**
- **Trigger:** `damage_taken`, mark tracking
- **Effect:**
  - Each attacker gets "Vengeance Mark" stack
  - Marked enemies take +10% counter damage per mark (stacking)
  - At 5 marks: Auto-counter on marked enemy's turn (proactive)
  - Marks persist entire combat
  - Counter attacks spread marks to nearby unmarked enemies
- **Synergies:** Multi-target scaling, mark synergy
- **Tuning Knobs:** Mark threshold, damage scaling, spread radius

**UI/Log Notes:**
- Visual mark/brand on enemy
- Log: "Vengeance Mark applied! ({X} marks)"

---

## Recommendations

**Current Implementation Strong:**
- Stack→burst mechanic creates satisfying payoff moments
- Infinite scaling with soft cap balances well
- Clear feedback loop (take damage→get stronger→burst)

**Suggested Refinements:**
1. Add visual telegraph before burst (warning flash at 45+ stacks)
2. Consider making mitigation buff scale with stacks
3. Log messages for stack milestones (25, 50, 75, 100)

**For Higher Tiers:**
- Prime: Lower burst threshold (30 stacks), multi-target bursts
- Boss: Mandatory counter phases, reflect mechanics
- Glitched: Random counter targets, stack volatility
