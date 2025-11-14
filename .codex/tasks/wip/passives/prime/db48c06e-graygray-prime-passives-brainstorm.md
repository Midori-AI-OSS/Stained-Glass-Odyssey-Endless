# Task: Brainstorm Prime Tier Tagged Passives for Graygray

## Background
Graygray's core moveset and lore live in `backend/plugins/characters/graygray.py`. We still need prime-tag passives that feel like exalted upgrades layered on the base kit so future Tier-Prime work has a clear head start. This is an ideation task only—capture concepts Coders can later formalize inside `backend/plugins/passives/prime/graygray.py`.

## Brainstorm Focus
- Emphasize mastery, efficiency, or awe-inspiring combos unlocked only at prime difficulty.
- Tie boosts to signature mechanics (unique resources, summons, weapon swaps, etc.).
- Ensure counters exist via timing, dispels, or resource denial so the fight remains interactive.

## Deliverables
- Capture all brainstorming directly inside this Markdown file; do not link out to other docs.
- Provide **three to five** candidate passive concepts tailored to this tag.
- For each option list: name, one-sentence fantasy hook, mechanical outline (trigger + effect), synergy callout to existing weapons/skills/resources, and any tuning knobs or risks. Explain what makes each idea “prime worthy” compared to the normal kit.
- Include at least one note on UI/log copy or telegraph ideas so the behaviour can be surfaced in game.
- Call out open questions that need design buy-in (stack caps, cooldown windows, conflicting systems, etc.).

## Reference Material
- Character plugin: `backend/plugins/characters/graygray.py`
- Tier guidance: `.codex/tasks/passives/prime/AGENTS.md`
- Existing passives directory for tone/language examples.

## Acceptance Criteria
- Document lists at least three well-explained concepts that match the character fantasy and the prime tier brief.
- Ideas stay within the tag's power band and leave room for other tiers to escalate separately.
- Notes clearly separate must-have behaviour from optional stretch goals.
- No code changes are performed as part of this task—output is a written brainstorming brief ready for review.

---

## Brainstormed Prime Concepts

### Option 1: Chain Counter Mastery (Recommended)
**Fantasy Hook:** Prime Graygray's counters trigger chain reactions, hitting multiple enemies simultaneously.

**Mechanics:**
- Burst threshold reduced to 30 stacks (from 50)
- Burst damage chains to 2 nearest enemies (75% damage each)
- Each chain hit applies 10 counter stacks to Graygray
- ATK scaling improved: +7.5% per stack (first 50), +4% after
- At 100 stacks: "Perfect Counter" state - all attacks counter automatically for 3 turns

**Prime-Worthy:** Multi-target threat, accelerated scaling, ultimate power state.

**UI/Log Notes:**
- Chain lightning effect between targets
- Log: "Chain Counter! {X} enemies hit!"
- Perfect Counter announces with screen flash

**Counterplay:** Spread positioning, burst before Perfect Counter state

---

### Option 2: Retribution Aura
**Fantasy Hook:** Prime Graygray radiates counter energy, punishing all nearby attackers.

**Mechanics:**
- Passive aura: Enemies within radius take 25% of damage they deal as reflection
- Counter stacks build 2× faster (2 per hit)
- At 40 stacks: Aura expands and intensifies (50% reflection, larger radius)
- Burst creates shockwave that stuns all enemies in aura for 1 turn

**Prime-Worthy:** Area control, passive threat without direct action.

**UI/Log Notes:**
- Visible red aura pulsing around Graygray
- Reflection damage shows as dark energy returning to attacker

---

### Option 3: Adaptive Counter
**Fantasy Hook:** Prime Graygray learns enemy patterns, countering with increasing precision.

**Mechanics:**
- Track damage types received; gain resistance (+5% per hit, max 30% per type)
- Counter damage type matches attacker's weakness
- "Learning" bonus: Each unique attacker adds +10% counter damage vs that enemy
- At 60 total counters: Unlock "Master" mode - predict and preemptively counter next attack

**Prime-Worthy:** Adaptive defense, pattern recognition, skill expression.

**UI/Log Notes:**
- Resistance bars show adaptation progress
- Log: "Pattern learned! Weakness detected!"

---

## Recommendations
**Primary: Chain Counter Mastery** - Best captures prime power scaling with multi-target threat.
**Alternative: Retribution Aura** - If prime needs zone control and passive damage.
