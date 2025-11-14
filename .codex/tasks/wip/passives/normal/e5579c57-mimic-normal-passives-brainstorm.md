# Task: Brainstorm Normal Tier Tagged Passives for Mimic

## Background
Mimic's core moveset and lore live in `backend/plugins/characters/mimic.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/mimic.py`.

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
- Character plugin: `backend/plugins/characters/mimic.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Normal: Player Copy (IMPLEMENTED)
**Mechanics:** Copies/mimics opponent abilities, adaptive playstyle, mirrors stats/skills.
**Options:** 1) Perfect copy (100% accuracy), 2) Improved copy (enhanced version), 3) Fusion copy (combines multiple targets)

## Prime: Master Mimic
- Copy 2-3 targets simultaneously, Mimicked abilities improved (+50% effectiveness), Can copy ultimate abilities, "Perfect Imitation" mode: Become exact clone including appearance

## Boss: Identity Crisis
**Phases:** Mimic random player→Mimic strongest enemy→Mimic entire party (multi-form)→"True Form" (amalgamation of all copied abilities)

## Glitched: Copy Error
- Copies wrong targets (allies, self, objects), Abilities glitch (wrong effects, inverted, combined randomly), Can't stop copying (stuck mimicking), Identity corruption (stats from multiple sources conflict)
