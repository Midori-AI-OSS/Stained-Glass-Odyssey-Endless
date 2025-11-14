# Task: Brainstorm Boss Tier Tagged Passives for Ixia

## Background
Ixia's core moveset and lore live in `backend/plugins/characters/ixia.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/ixia.py`.

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
- Character plugin: `backend/plugins/characters/ixia.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Boss Concepts

### Colossus Awakening (Recommended)
**Multi-Phase Encounter:**
- **Phase 1 (100-66%):** Normal Tiny Titan + 2 VIT/turn passive gain
- **Phase 2 (66-33%):** "Growth Spurt"
  - Size doubles visually
  - VIT→ATK = 1000%
  - All attacks become AoE cleaves
  - Stomp attacks apply tremor (movement slow)
- **Phase 3 (33-0%):** "Kaiju Mode"
  - Screen-filling presence
  - VIT→ATK = 1500%
  - Environmental damage (arena hazards)
  - Ground pounds create shockwaves
  - At 250 VIT: Arena-wide "Titan's Fall" (wipe threat)

### Unstoppable Force
- Cannot be stunned, slowed, or displaced
- Gains VIT equal to all CC attempts (immunity converts to power)
- Each failed CC: +10% movement speed (stacking)
- Enrage at 5 min: Double VIT gain, permanent berserker state

### Titanic Endurance
- HP cannot drop below 30% until VIT threshold reached
- Players must reduce VIT to enable damage (dispels, drains)
- Regenerates VIT over time (10/turn)
- Phase transition at VIT breakpoints rather than HP

**Recommendations:** Colossus Awakening for cinematic multi-phase experience.
