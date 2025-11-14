# Task: Brainstorm Normal Tier Tagged Passives for Mezzy

## Background
Mezzy's core moveset and lore live in `backend/plugins/characters/mezzy.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/mezzy.py`.

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
- Character plugin: `backend/plugins/characters/mezzy.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Normal: Gluttonous Bulwark (IMPLEMENTED)
**Mechanics:** Damage reduction, stat siphoning from enemies, absorbs portion of damage as temp HP/stats.
**Options:** 1) Feast mode (consume debuffs for power), 2) Overflow hunger (bonus at high absorption), 3) Shared feast (team benefits)

## Prime: Insatiable Appetite
- Absorption rate 2×, Siphon permanent stat boosts (not temporary), At 100 absorbed stats: "Glut Mode" (invulnerable + reflect for 2 turns), Can absorb ally buffs willingly for emergency power

## Boss: The Devourer
**Phases:** Normal absorption→Mass Siphon (drains all enemies each turn)→"True Hunger" (starts eating terrain, growing larger)→Singularity (becomes black hole, pulls enemies in)

## Glitched: Corrupted Consumption
- Absorption inverts randomly (loses stats instead), Siphoned stats go to random units, Can accidentally eat allies, Hunger meter displays backwards or corrupted, Temporary stat buffs become permanent debuffs
