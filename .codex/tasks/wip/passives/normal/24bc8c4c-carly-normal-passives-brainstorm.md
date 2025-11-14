# Task: Brainstorm Normal Tier Tagged Passives for Carly

## Background
Carly's core moveset and lore live in `backend/plugins/characters/carly.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/carly.py`.

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
- Character plugin: `backend/plugins/characters/carly.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the normal tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Concepts

### Current Implementation: Guardian's Aegis (IMPLEMENTED)
**Fantasy Hook:** Carly converts offensive power into defensive strength, healing allies while building impenetrable mitigation.

**Mechanics:**
- **Trigger:** `turn_start`
- **Effect:**
  - Converts any ATK growth into permanent DEF stacks (1:1 below 50 stacks, 1:0.5 after)
  - Heals most injured ally (or self) each turn
  - At 50+ mitigation stacks: Enter "Overcharged" state
    - Gain ATK bonus equal to current DEF
    - Lose 5 mitigation stacks per turn
    - Exit at ≤10 stacks
  - Passive aggro manipulation (+499 aggro modifier)
- **Synergies:** Punishes ATK buffs, rewards defensive stat stacking
- **Tuning Knobs:** Stack cap soft limit (50), overcharge threshold, heal amount

**UI/Log Notes:**
- Stack display shows mitigation level (0-50+)
- Overcharged state indicated by golden glow
- Log: "Guardian's Aegis: {X} defense stacks"

**Gameplay Loop:** Tank who gets stronger the longer she protects allies. ATK buffs backfire by fueling defense instead.

---

### Option 1: Light Barrier Accumulation
**Fantasy Hook:** Each time Carly blocks or tanks damage, she accumulates light energy for stronger barriers.

**Mechanics:**
- **Trigger:** `damage_taken`, `turn_start`
- **Effect:**
  - Gain 1 barrier stack per instance of damage taken (not amount)
  - At 5 stacks: Generate temporary shield for lowest HP ally (20% their max HP)
  - At 10 stacks: Refresh all active shields and extend duration
  - Stacks decay by 2 per turn if no damage taken
- **Synergies:** Rewards tanking hits, protects allies proactively
- **Tuning Knobs:** Stack thresholds, shield strength, decay rate

**UI/Log Notes:**
- Light particles accumulate around Carly with each hit
- Log: "Light Barrier activated on {ally}!"

**Open Questions:** Should shields stack or refresh? Max shields per ally?

---

### Option 2: Sacrificial Redirection
**Fantasy Hook:** Carly intercepts damage meant for allies, converting it into healing for the team.

**Mechanics:**
- **Trigger:** Ally takes damage (passive intercept check)
- **Effect:**
  - 30% chance to redirect ally damage to Carly
  - Damage redirected is reduced by 50%
  - For each 100 damage redirected, heal weakest ally for 25 HP
  - Track total redirected damage for bonus effects
- **Synergies:** Active tanking, team sustainability
- **Tuning Knobs:** Intercept %, damage reduction, heal conversion rate

**UI/Log Notes:**
- Visual beam connecting Carly to protected ally during redirect
- Log: "Carly intercepts the blow!"

**Risks:** Might make Carly too suicidal; needs HP scaling

---

### Option 3: Defensive Resonance
**Fantasy Hook:** Carly's presence strengthens allies' defenses through shared protective aura.

**Mechanics:**
- **Trigger:** `turn_start`, ally position updates
- **Effect:**
  - Grant nearby allies +10% DEF per turn (stacking, max +50%)
  - If Carly has 30+ DEF, share 20% of it with all allies
  - Bonus doubles for allies below 50% HP
- **Synergies:** Team-wide mitigation, scales with Carly's defense
- **Tuning Knobs:** Aura radius, DEF sharing %, bonus thresholds

**UI/Log Notes:**
- Glowing aura emanating from Carly to nearby allies
- Log: "Defensive Resonance strengthens the party!"

**Open Questions:** Should this persist if Carly is KO'd?

---

## Recommendations

**Current Implementation is Strong:**
- ATK→DEF conversion is unique and fits tank fantasy
- Overcharged state provides offensive option without compromising role
- Clear progression curve with soft cap at 50 stacks

**Suggested Refinements:**
1. Add more granular healing targeting (prioritize tanks vs damage dealers)
2. Visual feedback for mitigation stacks accumulation
3. Consider diminishing returns past 100 stacks to prevent runaway scaling

**For Higher Tiers:**
- Prime: Faster stack accumulation, team-wide mitigation sharing
- Boss: Multi-phase overcharge cycles, threat mechanics
- Glitched: Unpredictable ATK/DEF conversions, barrier malfunctions
