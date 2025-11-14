# Task: Brainstorm Prime Tier Tagged Passives for Carly

## Background
Carly's core moveset and lore live in `backend/plugins/characters/carly.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/carly.py`.

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
- Character plugin: `backend/plugins/characters/carly.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the prime tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Prime Concepts

### Option 1: Aegis Amplification (Recommended)
**Fantasy Hook:** Prime Carly's barriers become so strong they reflect damage back and shield the entire party.

**Mechanics:**
- **Trigger:** `turn_start`, mitigation stack thresholds
- **Effect:**
  - ATK→DEF conversion rate improved (1:1 up to 75 stacks, then 1:0.75)
  - At 40+ stacks: Grant team-wide damage reduction (10% party-wide)
  - At 60+ stacks: Barriers reflect 25% of incoming damage to attackers
  - Overcharge triggers at 75 stacks instead of 50
  - Overcharge grants DEF×1.5 as ATK (up from DEF×1.0)
- **Synergies:** Amplifies base tank mechanics, adds team utility and counterattack
- **Tuning Knobs:** Stack thresholds, reflection %, team reduction %

**Prime-Worthy:** Scales defensive power into zone control and team support.

**UI/Log Notes:**
- Shimmering barrier visible around entire party at 40+ stacks
- Reflected damage shows as golden light beam from Carly to attacker
- Log: "Aegis Amplification: Party shielded! ({X} stacks)"

**Counterplay:** Dispel stacks, burst damage before thresholds, multi-wave attacks

---

### Option 2: Martyr's Resolve
**Fantasy Hook:** Prime Carly can sacrifice her defense to instantly save allies from lethal damage.

**Mechanics:**
- **Trigger:** Ally drops below 15% HP
- **Effect:**
  - Auto-activate: Consume 20 mitigation stacks to prevent ally death
  - Ally is healed to 40% HP instantly
  - Carly gains "Resolute" buff: +50% healing received for 3 turns
  - Can trigger once per ally per combat
  - If Carly has 80+ stacks, only costs 10 stacks
- **Synergies:** Ultimate clutch save, rewards high stack accumulation
- **Tuning Knobs:** Stack cost, heal amount, cooldown per ally

**Prime-Worthy:** Adds dramatic save moments and strategic resource management.

**UI/Log Notes:**
- Dramatic golden beam from Carly to dying ally
- Screen flash and sound effect on activation
- Log: "Martyr's Resolve! {Ally} is saved!"

**Open Questions:** Should there be global cooldown to prevent spamming?

---

### Option 3: Radiant Overcharge
**Fantasy Hook:** Prime overcharge state becomes a sustained offensive mode rather than temporary burst.

**Mechanics:**
- **Trigger:** Overcharge activation, stack management
- **Effect:**
  - Overcharge no longer decays stacks over time
  - Instead: Choose to "lock" at current mitigation level
  - Locked overcharge grants: ATK = DEF × 1.75
  - Can manually exit overcharge to resume stack building
  - Re-entering requires returning to threshold
  - While overcharged: Healing output doubled
- **Synergies:** Adds strategic timing, offense/defense mode switching
- **Tuning Knobs:** ATK multiplier, healing bonus, lock duration

**Prime-Worthy:** Transforms burst into sustained power stance.

**UI/Log Notes:**
- Toggle indicator: "Overcharge: LOCKED" vs "Overcharge: BUILDING"
- Visual: Sustained golden aura vs pulsing glow
- Log: "Radiant Overcharge locked! ({X} DEF = {Y} ATK)"

**Risks:** Might be too strong if locked indefinitely; consider adding drawbacks

---

### Option 4: Sanctified Ground
**Fantasy Hook:** Prime Carly creates zones of protection that persist and strengthen over time.

**Mechanics:**
- **Trigger:** `turn_end`, healing activations
- **Effect:**
  - Each heal creates "Sanctified Zone" at recipient's location
  - Zones grant: +15 DEF, +5% healing received to allies standing in them
  - Zones last 5 turns, stack up to 3 zones per location
  - At 50+ mitigation stacks: Zones also deal holy damage to enemies (5% max HP/turn)
  - Max 4 zones active simultaneously
- **Synergies:** Territory control, positioning rewards, area denial
- **Tuning Knobs:** Zone duration, buff strength, damage output, max zones

**Prime-Worthy:** Adds battlefield manipulation to tank role.

**UI/Log Notes:**
- Glowing golden circles on ground showing zone locations
- Zone intensity increases with stacks
- Log: "Sanctified Ground established at {location}!"

**Counterplay:** Force repositioning, dispel zones, mobility challenges

---

## Recommendations

**Primary: Aegis Amplification**
- Natural extension of base mechanic
- Adds team utility (prime fantasy)
- Reflection creates counterattack threat
- Clear thresholds for power spikes

**Alternative: Martyr's Resolve**
- If prime needs clutch save mechanics
- Very thematic for protection fantasy
- Creates memorable moments

**Consider: Radiant Overcharge**
- If overcharge needs more strategic depth
- Mode-switching adds skill expression
