# Task: Brainstorm Glitched Tier Tagged Passives for Ixia

## Background
Ixia's core moveset and lore live in `backend/plugins/characters/ixia.py`. We still need glitched-tag passives that warp the character's behavior in unpredictable or corrupted ways so future Tier-Glitched work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/glitched/ixia.py`.

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
- Character plugin: `backend/plugins/characters/ixia.py`
- Tier guidance: `.codex/tasks/passives/glitched/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Glitched Concepts

### Size Corruption (Recommended)
- Size fluctuates unpredictably each turn:
  - 40%: Microscopic (1% normal size) - high evasion, no damage
  - 40%: Normal size - standard mechanics
  - 20%: Colossal (500% size) - huge hitbox, massive damage
- VIT conversions glitch:
  - Random multipliers: 100%-2000% for ATK conversion
  - HP conversion can invert (lose HP per VIT)
- Collision detection errors cause random teleportation
- At 200 VIT: Size becomes "undefined" (invisible + invulnerable for 1 turn)

### Quantum Titan
- Exists in multiple size states simultaneously
- Damage calculations use random size value
- Hit chance vs Ixia: 33% (might phase out)
- Attacks hit random number of times (1-5) based on size uncertainty

### Stat Overflow
- VIT counter can overflow at 255 (wraps to 0)
- Negative VIT possible (becomes giant weakness)
- Conversions use absolute value (negative VIT still grants ATK)
- Display shows corrupted values: "VIT: ��#"

**Recommendations:** Size Corruption for visual chaos and learnable patterns.
