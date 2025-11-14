# Task: Brainstorm Normal Tier Tagged Passives for Ryne

## Background
Ryne's core moveset and lore live in `backend/plugins/characters/ryne.py`. We still need baseline tagged passive concepts used when no encounter modifiers are present so future Tier-Normal work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/normal/ryne.py`.

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
- Character plugin: `backend/plugins/characters/ryne.py`
- Tier guidance: `.codex/tasks/passives/normal/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
[...]

---

## Normal: Oracle of Balance (IMPLEMENTED)
**Mechanics:** Balance system - tracks party/enemy HP ratios, grants bonuses when balanced, penalties when imbalanced, equilibrium state.
**Options:** 1) Forced balance (damage redistribution), 2) Perfect harmony (bonus at 50/50), 3) Chaos from imbalance

## Prime: Cosmic Equilibrium
- Balance window wider (40-60% instead of 45-55%), Equilibrium grants team-wide buffs (not just Ryne), Can force balance (redistribute HP between allies), "Perfect Balance" state at exact 50/50: Time dilation (extra turn for team)

## Boss: Scales of Fate
**Phases:** Gentle nudges→Forced equilibrium (constant HP redistribution)→"Universal Balance" (all units locked to 50% HP)→Judgment (executes imbalanced side)

## Glitched: Chaotic Scales
- Balance calculations corrupted (uses random stats instead of HP), Equilibrium inverts effects (bonuses become penalties), Balance can force negative HP (instant death), Display shows impossible ratios ("150%/−50%")
