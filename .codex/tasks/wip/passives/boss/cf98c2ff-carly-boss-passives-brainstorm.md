# Task: Brainstorm Boss Tier Tagged Passives for Carly

## Background
Carly's core moveset and lore live in `backend/plugins/characters/carly.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/carly.py`.

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
- Character plugin: `backend/plugins/characters/carly.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the boss tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Boss Concepts

### Option 1: Impenetrable Fortress (Recommended)
**Fantasy Hook:** Boss Carly becomes an unstoppable defensive juggernaut with escalating threat phases.

**Mechanics:**
- **Trigger:** `turn_start`, HP thresholds, mitigation milestones
- **Effect:**
  - Stack cap removed (unlimited growth)
  - **Phase 1 (100-75% HP):** Normal mechanics, gain 3 stacks/turn baseline
  - **Phase 2 (75-50% HP):** "Fortress Mode"
    - Immune to ATK buffs (instant DEF conversion)
    - Team-wide 25% damage reduction aura
    - Overcharge ATK multiplier = DEF × 2.0
  - **Phase 3 (50-25% HP):** "Unbreakable"
    - Gain 5 stacks/turn
    - Reflect 50% of all damage taken
    - Heals for 10% missing HP each turn
  - **Phase 4 (<25% HP):** "Last Stand"
    - Cannot be reduced below 1 HP for 3 turns
    - All allies gain Carly's DEF as bonus HP shield
    - Permanent overcharge state
- **Synergies:** Multi-phase encounter, escalating difficulty
- **Tuning Knobs:** Phase HP thresholds, stack gain rates, immunity duration

**Boss-Worthy:** Creates structured encounter with clear phase transitions and mounting threat.

**UI/Log Notes:**
- Phase announcements with screen effects
- Visual: Barrier intensity increases with each phase
- Fortress glow, unbreakable crystalline effect, last stand golden nova
- Log: "PHASE 2: Fortress Mode activated!"
- HP bar shows phase markers

**Counterplay:** 
- Phase 1: Build damage quickly
- Phase 2: Dispel team aura, focus fire
- Phase 3: Reduce healing, manage reflections
- Phase 4: Survive last stand, exhaust immunity

---

### Option 2: Aegis Network
**Fantasy Hook:** Boss Carly creates interconnected shields that protect all enemies while draining attackers.

**Mechanics:**
- **Trigger:** `turn_start`, combat state
- **Effect:**
  - Grant all allied enemies "Aegis Link" buff
  - Linked enemies share 50% of damage taken with Carly
  - Carly converts shared damage into mitigation stacks (10 damage = 1 stack)
  - At 100+ stacks: Link becomes two-way
    - Carly's attacks heal linked allies for 20% damage dealt
    - Linked allies gain +30% DEF
  - Destroying a linked enemy transfers stacks to Carly
- **Synergies:** Forces target prioritization, punishes AoE
- **Tuning Knobs:** Damage sharing %, conversion rate, link count

**Boss-Worthy:** Transforms boss into raid encounter with add management.

**UI/Log Notes:**
- Golden chains visible connecting Carly to linked enemies
- Damage numbers split between targets
- Log: "Aegis Network established! Enemies shielded."

**Counterplay:** Focus fire on Carly first, dispel links, single-target damage

---

### Option 3: Overcharge Cascade
**Fantasy Hook:** Boss Carly cycles between extreme offense and defense rapidly, forcing adaptation.

**Mechanics:**
- **Trigger:** Automatic timing, stack thresholds
- **Effect:**
  - Forced overcharge at 40 stacks (instead of 50)
  - Overcharge lasts exactly 3 turns, then mandatory 2-turn cooldown
  - During overcharge:
    - ATK = DEF × 3.0
    - Actions per turn +50%
    - Takes double damage
  - During cooldown:
    - Gain 10 stacks/turn rapidly
    - 75% damage reduction
    - Cannot attack
  - **Enrage at 5 minutes:** Overcharge becomes permanent
- **Synergies:** Creates timing windows for burst/defense
- **Tuning Knobs:** Cycle durations, multipliers, enrage timer

**Boss-Worthy:** Requires careful timing and phase management.

**UI/Log Notes:**
- Cycle timer visible: "Overcharge: 2 turns remaining"
- Visual: Aggressive pulsing (overcharge) vs slow glow (cooldown)
- Log: "Overcharge Cascade! Vulnerability window!"
- Enrage warning at 4:30

**Counterplay:** Burst during overcharge windows, survive cooldown phases

---

### Option 4: Divine Intervention
**Fantasy Hook:** Boss Carly can resurrect defeated allies with protective blessings.

**Mechanics:**
- **Trigger:** Allied enemy death, turn thresholds
- **Effect:**
  - Every 5 turns, can resurrect 1 defeated enemy at 50% HP
  - Resurrected enemy gains "Divine Blessing":
    - Immune to death for 2 turns
    - +50% all stats
    - Shares vision with Carly (linked targeting)
  - Consumes 25 mitigation stacks per resurrection
  - Max 3 resurrections per combat
  - **Ultimate:** At 150+ stacks, resurrect ALL defeated enemies
- **Synergies:** Makes killing adds temporary, attrition warfare
- **Tuning Knobs:** Resurrection frequency, blessing strength, stack cost

**Boss-Worthy:** Forces sustained pressure and resource management.

**UI/Log Notes:**
- Resurrection countdown timer: "Intervention in: X turns"
- Glowing ankh symbol appears on corpse before resurrection
- Log: "Divine Intervention! {Enemy} rises again!"
- Blessed enemies glow with golden aura

**Counterplay:** Burn down Carly first, dispel blessings, save burst for post-resurrection

---

## Recommendations

**Primary: Impenetrable Fortress**
- Clear four-phase structure
- Escalating difficulty curve
- Multiple mechanics to learn
- Satisfying final phase

**Alternative: Aegis Network**
- If boss encounter needs adds/minions
- Creates tactical target priority puzzle
- Rewards coordination

**Complex Option: Overcharge Cascade + Divine Intervention**
- Combine for ultimate difficulty
- Timing + resource management
- Very challenging but learnable
