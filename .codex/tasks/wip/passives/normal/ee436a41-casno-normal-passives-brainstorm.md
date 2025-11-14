# Task: Brainstorm Normal Tier Tagged Passives for Casno

## Background
Casno's core moveset and lore live in `backend/plugins/characters/casno.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/casno.py`.

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
- Character plugin: `backend/plugins/characters/casno.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Normal: Phoenix Respite (IMPLEMENTED)
**Mechanics:** Relaxed momentum system - healing pulse every few turns, scales with "relaxation" (time not acting offensively).
**Options:** 1) Meditation stacks, 2) Emergency burn (sacrifice relaxation for burst heal), 3) Aura expansion (range increases with stacks)

## Prime: Phoenix Ascendant  
- HoT magnitude 2×, Relaxed momentum builds 50% faster, at max relaxation: Party-wide revive (once/combat), flames never fully extinguished

## Boss: Eternal Flame
**Phases:** Normal→Self-Resurrection (at death, revive once at 50% HP)→Immolation (permanent fire aura, constant healing)→Phoenix Rebirth (death triggers team-wide resurrection)

## Glitched: Unstable Combustion
- Healing randomized (0-300% normal), momentum corrupted (can go negative), "relaxation" becomes "agitation" (heals on attacking instead), flames flicker in/out unpredictably
