# Task: Brainstorm Boss Tier Tagged Passives for Ryne

## Background
Ryne's core moveset and lore live in `backend/plugins/characters/ryne.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/ryne.py`.

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
- Character plugin: `backend/plugins/characters/ryne.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Boss: Scales of Fate (Recommended)
**Phase 1 (100-75%):** Passive balance monitoring + gentle HP nudges toward equilibrium
**Phase 2 (75-50%):** Forced Equilibrium - automatic HP redistribution every turn, pulls both sides toward 50%
**Phase 3 (50-25%):** Universal Balance - all units' HP locked to percentage ranges (can't exceed/fall below), constant rebalancing
**Phase 4 (<25%):** Judgment Day - "The Scales Demand Payment" - side with lower total HP receives execute damage, must maintain exact balance or wipe

## Boss: Inevitable Equilibrium
- Passive balance aura (all units slowly trend toward 50% HP), Healing reduced by 75% (prevents escape from balance), Damage capped at 10% per hit (prevents burst), At 5 minutes: "Perfect Balance" forces all units to exactly 50% HP permanently

**Recommendations:** Scales of Fate for dramatic multi-phase balance puzzle.
