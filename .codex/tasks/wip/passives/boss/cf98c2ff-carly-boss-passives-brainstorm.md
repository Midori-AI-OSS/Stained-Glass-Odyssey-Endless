# Task: Brainstorm Boss Tier Tagged Passives for Carly

## Background
Carly's core moveset and lore live in `backend/plugins/characters/carly.py`. We still need boss-tagged passives that make the character feel like a climactic encounter so future Tier-Boss work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/boss/carly.py`.

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
- Character plugin: `backend/plugins/characters/carly.py`
- Tier guidance: `.codex/tasks/passives/boss/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the boss tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.
