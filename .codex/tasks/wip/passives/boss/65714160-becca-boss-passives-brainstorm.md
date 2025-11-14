# Task: Brainstorm Boss Tier Tagged Passives for Becca

## Background
Becca's core moveset and lore live in `backend/plugins/characters/becca.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/becca.py`.

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
- Character plugin: `backend/plugins/characters/becca.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Boss: Aquatic Legion (Recommended)
**Phase 1:** 1-2 pets baseline
**Phase 2 (75%):** 4 active pets, pets respawn every 2 turns
**Phase 3 (50%):** Unlimited pet spawning (1 per turn), pets stronger
**Phase 4 (25%):** Pets merge into "Mega-Jellyfish" (Becca pilots from inside), shared HP pool, massive AoE attacks, tentacle swarm

## Boss: Tidal Swarm
- Passive pet generation (1 every 2 turns automatically), Pets explode on death (AoE damage), At 15 pets killed: "Swarm Frenzy" enrage (all pet stats doubled), Becca becomes invulnerable while pets alive

**Recommendations:** Aquatic Legion for cinematic transformation finale.
