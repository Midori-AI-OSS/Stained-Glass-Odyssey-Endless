# Task: Brainstorm Boss Tier Tagged Passives for Graygray

## Background
Graygray's core moveset and lore live in `backend/plugins/characters/graygray.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/graygray.py`.

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
- Character plugin: `backend/plugins/characters/graygray.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the boss tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Boss Concepts

### Option 1: Infinite Retaliation (Recommended)
**Fantasy Hook:** Boss Graygray enters escalating counter phases, becoming unstoppable.

**Mechanics:**
- **Phase 1 (100-75% HP):** Normal counters, 40 stack bursts
- **Phase 2 (75-50%):** All damage triggers immediate counter (no stack needed), bursts at 30
- **Phase 3 (50-25%):** Counter damage scales with missing HP (+1% per 1% HP lost), bursts at 20
- **Phase 4 (<25%):** "Berserk Maestro" - Automatic counters on ALL enemy actions (even non-damage), burst every 10 stacks, immune to CC

**Boss-Worthy:** Four-phase escalation, mounting threat, dramatic final phase.

**UI/Log Notes:**
- Phase announcements
- Counter flurry visual effects
- Log: "BERSERK MAESTRO ACTIVATED!"

**Counterplay:** Burst early phases, manage damage output in late phases, coordinate burst windows.

---

### Option 2: Vengeful Echo
**Fantasy Hook:** Boss Graygray's fallen allies return as counter echoes.

**Mechanics:**
- When ally dies, spawn "Vengeance Echo" (spirit minion)
- Echoes inherit 50% of Graygray's counter stacks
- Echoes auto-counter any damage dealt in their zone
- At 150 total stacks (combined): Mass resurrection of all echoes at full power
- Graygray gains +20% stats per active echo

**Boss-Worthy:** Minion management, resurrection mechanic, scaling threat.

**UI/Log Notes:**
- Ghost/spirit visual for echoes
- Stack counter shows Graygray + Echo total

---

### Option 3: Counter Singularity
**Fantasy Hook:** Boss accumulates so much counter energy it creates a damage vortex.

**Mechanics:**
- Stacks never consumed by bursts
- At 100/200/300 stacks: Create pulsing damage zone
- Zone deals % of Graygray's ATK as AoE every turn
- Multiple zones stack damage
- At 500 stacks: "Singularity Collapse" - massive arena-wide burst, reset to 0

**Boss-Worthy:** Escalating environmental hazard, soft enrage at 500.

**UI/Log Notes:**
- Pulsing red zones on battlefield
- Singularity countdown at 400+ stacks

---

## Recommendations
**Primary: Infinite Retaliation** - Clear phase structure with dramatic escalation.
