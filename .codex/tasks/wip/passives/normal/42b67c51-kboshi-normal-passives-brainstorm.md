# Task: Brainstorm Normal Tier Tagged Passives for Kboshi

## Background
Kboshi's core moveset and lore live in `backend/plugins/characters/kboshi.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/kboshi.py`.

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
- Character plugin: `backend/plugins/characters/kboshi.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Normal: Flux Cycle (IMPLEMENTED)
**Mechanics:** Random element rotation each turn, stacking HoT, damage bonuses per element switch.
**Fantasy:** Elemental chaos master cycling through damage types.
**Options:** 1) Elemental memory (bonus for repeated types), 2) Flux resonance (matching ally elements), 3) Overload release (burst at max stacks)

## Prime: Harmonic Convergence
- Attune to 2 elements simultaneously (dual damage), faster cycling, perfect flux state at 5 unique elements cycled grants "Prismatic Overload" (all elements at once for 2 turns)

## Boss: Chaotic Maelstrom
**Phases:** Normal→Accelerated (2 elements/turn)→Unstable (random switching mid-turn)→Elemental Singularity (all elements always, massive AoE)

## Glitched: Element Corruption
- Random "null" element (no damage type), inverted elements (fire heals instead of burns), impossible elements ("quantum", "void"), element can change mid-attack
