# Eclipse Reactor: burst-for-blood 5★ relic

## Summary
Our 5★ set covers high-risk ally sacrifice (Paradox Hourglass), attrition-focused revives (Soul Prism), and long-duration stat overclocks (Omega Core). We still lack a relic that trades a chunk of HP for an explosive short-term power spike before decaying into a drain, giving aggressive players a distinct pacing lever.【F:backend/plugins/relics/paradox_hourglass.py†L13-L160】【F:backend/plugins/relics/soul_prism.py†L11-L105】【F:backend/plugins/relics/omega_core.py†L13-L114】

## Details
* Create **Eclipse Reactor**: on `battle_start`, drain 18% Max HP per stack from every ally (non-lethal) and apply a 3-turn buff (+180% ATK, +180% SPD, +60% crit damage per stack) representing the eclipse surge. When the buff expires, allies begin taking 2% Max HP damage per stack each turn for the remainder of the battle until combat ends.
* Use RelicBase helpers to apply the temporary stat multipliers via `create_stat_buff`, then schedule a follow-up hook that swaps to the post-surge HP drain. Follow Omega Core's pacing for long-duration buffs and Greed Engine's HP drain approach for the aftermath.【F:backend/plugins/relics/omega_core.py†L14-L120】【F:backend/plugins/relics/greed_engine.py†L18-L68】
* Emit telemetry for both the initial drain and the buff activation/expiration so the battle log clearly reflects the trade-offs.【F:backend/plugins/relics/omega_core.py†L61-L102】

## Requirements
- Implement `backend/plugins/relics/eclipse_reactor.py` with clear state tracking (storing remaining surge duration, hooking `turn_start` to apply the post-surge drain) and a descriptive `describe(stacks)` documenting both phases.
- Add comprehensive tests covering: initial HP drain clamping at 1 HP, buff duration stacking, transition into the post-surge drain, and cleanup on battle end. Extend `backend/tests/test_relic_effects_advanced.py` or add a new module.
- Include a thorough `about` string in the plugin summarising surge values, drain pacing, and stacking rules so the roster stays self-documented.
- Record a placeholder art prompt for Eclipse Reactor in `luna_items_prompts.txt` under **Missing Relics Art**, noting the relic slug so the Lead Developer can hand-create the icon later without blocking this task.【F:luna_items_prompts.txt†L11-L27】
- Capture balancing notes (HP drain math, buff multipliers) in `.codex/docs/relics/` for future tuning discussions.
