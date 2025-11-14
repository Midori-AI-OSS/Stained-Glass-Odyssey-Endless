# Task: Brainstorm Boss Tier Tagged Passives for Hilander

## Background
Hilander's core moveset and lore live in `backend/plugins/characters/hilander.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/hilander.py`.

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
- Character plugin: `backend/plugins/characters/hilander.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Boss Concepts

### Option 1: Critical Mass (Recommended)
**Four-Phase Escalation:**
- **Phase 1 (100-75%):** Normal fermentation, 15-stack release threshold
- **Phase 2 (75-50%):** "Unstable" - Auto-crit every 5 stacks, chain to 2 enemies
- **Phase 3 (50-25%):** "Volatile" - Stacks build on ALL actions (not just hits), forced crits every turn
- **Phase 4 (<25%):** "Detonation" - Permanent crit state, each hit applies ferment stacks to enemies (damage amplification)

**Boss-Worthy:** Clear phases, escalating threat, dramatic finale.

### Option 2: Crit Cascade Network
- All allied enemies gain shared ferment pool
- When any ally crits, all allies gain half the crit bonus
- Boss gains stacks when allies deal damage
- At 30 combined stacks: Mass critical strike from all enemies simultaneously

### Option 3: Enrage Timer
- Passive stack gain over time (1/turn baseline)
- At 50 stacks: "Critical Overload" - arena-wide crit explosion, reset
- Overload damage increases each cycle
- Soft enrage: 5-minute timer forces overload regardless of stacks

**Recommendations:** Critical Mass for structured encounter, Enrage Timer for DPS check.
